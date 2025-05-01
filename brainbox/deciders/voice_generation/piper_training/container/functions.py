import os
from pathlib import Path
import shutil
import subprocess
from settings import TrainingSettings
from typing import Optional
import re

class Functions:
    def __init__(self, dataset: str, working_dir: str, settings: Optional[TrainingSettings]):
        self.dataset = dataset
        self.working_dir = Path(working_dir)
        self.settings = settings


    def get_path(self):
        return self.working_dir/'trainings'/self.dataset

    def get_all_ckpt(self):
        i = 0
        preprocessed_path = self.get_path() / 'preprocessed'
        result = []
        while True:
            model_path = preprocessed_path / f'lightning_logs/version_{i}/checkpoints/'
            if not model_path.is_dir():
                break
            i += 1
            for model in os.listdir(model_path):
                match = re.match('epoch=(\d+)-step=(\d+)\.ckpt', model)
                if match is None:
                    continue
                result.append((model_path/model, int(match.group(1))))
        return [r[0] for r in sorted(result, key = lambda z: z[1])]


    def is_single_speaker(self):
        with open(self.get_path()/ 'source/metadata.csv', 'r') as file:
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
        source_path = self.get_path()/'source'
        preprocessed_path = self.get_path()/'preprocessed'
        single_speaker = self.is_single_speaker()

        shutil.rmtree(preprocessed_path, ignore_errors=True)

        subprocess.call([
            'python3',
            '-m',
            'piper_train.preprocess',
            '--language',
            self.settings.language,
            '--input-dir',
            str(source_path),
            '--output-dir',
            str(preprocessed_path),
            '--dataset-format',
            'ljspeech',
            *(['--single-speaker'] if single_speaker else []),
            '--sample-rate',
            str(self.settings.sample_rate)
        ])

    def train(self):
        preprocessed_path = self.get_path()/'preprocessed'

        resume = [
            '--resume_from_checkpoint',
            str(self.working_dir / 'base_models' / self.settings.base_model),
        ]

        if self.settings.continue_existing:
            all_models = self.get_all_ckpt()
            if len(all_models) == 0:
                raise ValueError("Cannot continue the training: no stored checkpoints are available")
            resume[1] = str(all_models[-1])
        elif self.settings.single_speaker_to_multi_speaker:
            resume[0] = '--resume_from_single_speaker_checkpoint'

        subprocess.call([
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
            str(self.settings.batch_size),
            '--validation-split',
            str(self.settings.validation_split),
            '--num-test-examples',
            str(self.settings.num_test_examples),
            '--max_epochs',
            str(self.settings.max_epochs),
            *resume,
            '--checkpoint-epochs',
            str(self.settings.checkpoint_epochs),
            '--precision',
            str(self.settings.precision),
            *(['--keep-intermediate'] if self.settings.keep_intermediate else []),
        ])

    def export_model(self):
        preprocessed_path = self.get_path()/'preprocessed'
        result_path = self.get_path()/'result'
        os.makedirs(result_path, exist_ok=True)
        for model in self.get_all_ckpt():
            parts = model.name.split('.')
            if len(parts) != 2:
                raise ValueError(f"Wrong filename format {model}")
            name, _ = parts
            Functions.convert_custom_filename(model, result_path)
            shutil.copy(
                preprocessed_path/'config.json',
                str(result_path/(name+'.onnx.json'))
            )

    @staticmethod
    def convert_custom_filename(path, target_folder = None):
        if target_folder is None:
            target_folder = path.parent
        name, extension = path.name.split('.')
        subprocess.call([
            'python3',
            '-m',
            'piper_train.export_onnx',
            str(path),
            str(target_folder / (name + ".onnx"))
        ])
