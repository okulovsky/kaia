import os
from pathlib import Path
import shutil
from interface import PiperTrainingParameters, CkptData
import re
from foundation_kaia.brainbox_utils import subprocess_streaming_call, LongBrainboxProcess, logger
import zipfile
from installer import PiperTrainingInstaller


class Loc:
    @staticmethod
    def get_training_folder(training_id: str) -> Path:
        return Path(f'/resources/training/{training_id}')

    @staticmethod
    def get_checkpoints_folder(training_id: str, version: str) -> Path:
        return Loc.get_training_folder(training_id) /  f'preprocessed/lightning_logs/version_{version}/checkpoints/'

    @staticmethod
    def get_checkpoint_path(ckpt: CkptData) -> Path:
        return Loc.get_checkpoints_folder(ckpt.training_id, ckpt.version) / ckpt.filename


class Training(LongBrainboxProcess[list[CkptData]]):
    def __init__(self,
                 training_id: str,
                 base_model: str,
                 parameters: PiperTrainingParameters,
                 installer: PiperTrainingInstaller,
                 ):
        self.training_id = training_id
        self.base_model = base_model
        self.parameters = parameters
        self.installer = installer
        self.training_folder = Loc.get_training_folder(self.training_id)

    def unzip_dataset(self):
        csv = []
        dataset_folder = self.training_folder / 'source'
        shutil.rmtree(dataset_folder, ignore_errors=True)
        os.makedirs(dataset_folder / 'wav')

        with zipfile.ZipFile(self.training_folder / 'dataset.zip', 'r') as file:
            for name in file.namelist():
                character, filename = name.split('/')
                if not filename.endswith('.wav'):
                    continue
                data = file.read(name)
                output_path = dataset_folder / 'wav' / filename
                with open(output_path, 'wb') as output_file:
                    output_file.write(data)
                text = file.read(name.replace('.wav', '.txt')).decode('utf-8')
                csv.append(dict(character=character, id=filename, text=text))
                logger.info(f"Character {character} id {filename} text {text}")

        single_speaker = len(set(c['character'] for c in csv)) == 1
        logger.info(f"Single speaker {single_speaker}")
        with open(dataset_folder / 'metadata.csv', 'w') as file:
            for record in csv:
                if single_speaker:
                    file.write(f'{record["id"]}|{record["text"]}\n')
                else:
                    file.write(f'{record["id"]}|{record["character"]}|{record["text"]}\n')
        logger.info("Metadata created")


    def is_single_speaker(self):
        with open(self.training_folder/ 'source/metadata.csv', 'r') as file:
            first_line = file.readline()
            groups = first_line.split('|')
            if len(groups) == 2:
                return True
            elif len(groups) == 3:
                return False
            else:
                raise ValueError(
                    f"Lines of csv files are supposed to have 2 or 3 parts separated by '|', but was\n{first_line}")


    def preprocess(self):
        source_path = self.training_folder/'source'
        preprocessed_path = self.training_folder/'preprocessed'
        single_speaker = self.is_single_speaker()

        shutil.rmtree(preprocessed_path, ignore_errors=True)
        model_spec = self.installer.get_model_spec(self.base_model)


        arguments = [
            'python3',
            '-m',
            'piper_train.preprocess',
            '--language',
            model_spec.language,
            '--input-dir',
            str(source_path),
            '--output-dir',
            str(preprocessed_path),
            '--dataset-format',
            'ljspeech',
            *(['--single-speaker'] if single_speaker else []),
            '--sample-rate',
            str(self.parameters.sample_rate)
        ]

        for line in subprocess_streaming_call(arguments):
            logger.info(line)



    def get_all_ckpt(self) -> list[CkptData]:
        i = 0
        result = []
        while True:
            version = str(i)
            model_path = Loc.get_checkpoints_folder(self.training_folder.name, version)
            if not model_path.is_dir():
                break
            i += 1
            for model in os.listdir(model_path):
                match = re.match('epoch=(\d+)-step=(\d+)\.ckpt', model)
                if match is None:
                    continue
                result.append(CkptData(self.training_folder.name, version, model, int(match.group(1)), int(match.group(2))))
        return result


    def train(self):
        preprocessed_path = self.training_folder/'preprocessed'

        resume = [
            '--resume_from_checkpoint',
            str(self.installer.base_models_folder/self.base_model),
        ]

        if self.parameters.continue_existing:
            all_models = self.get_all_ckpt()
            if len(all_models) == 0:
                raise ValueError("Cannot continue the training: no stored checkpoints are available")
            resume[1] = str(Loc.get_checkpoint_path(all_models[-1]))
        elif self.parameters.single_speaker_to_multi_speaker:
            resume[0] = '--resume_from_single_speaker_checkpoint'

        model_spec = self.installer.get_model_spec(self.base_model)

        arguments = [
            'python3',
            '-m',
            'piper_train',
            '--dataset-dir',
            str(preprocessed_path),
            '--accelerator',
            "cuda",
            '--devices',
            '1',
            '--batch-size',
            str(self.parameters.batch_size),
            '--validation-split',
            str(self.parameters.validation_split),
            '--num-test-examples',
            str(self.parameters.num_test_examples),
            '--max_epochs',
            str(self.parameters.epochs + model_spec.epoch),
            *resume,
            '--checkpoint-epochs',
            str(self.parameters.checkpoint_epochs),
            '--precision',
            str(self.parameters.precision),
            *(['--keep-intermediate'] if self.parameters.keep_intermediate else []),
        ]

        for line in subprocess_streaming_call(arguments):
            logger.info(line)
            ckpts = self.get_all_ckpt()
            if len(ckpts) == 0:
                logger.progress(0)
            else:
                max_epoch = max(c.epoch for c in ckpts)
                progress = (max_epoch - model_spec.epoch)/self.parameters.epochs
                logger.progress(progress)




    def execute(self) -> list[CkptData]:
        logger.info(f"Training parameters: {self.parameters}")

        with logger.section("Unpacking the dataset"):
            self.unzip_dataset()

        with logger.section("Recoding the dataset"):
            self.preprocess()

        with logger.section("Training the model"):
            self.train()

        return self.get_all_ckpt()
