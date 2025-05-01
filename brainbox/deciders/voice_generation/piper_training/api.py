from brainbox import BrainBoxApi, IBrainBoxTask
from brainbox.framework import OnDemandDockerApi, FileLike, FileIO, File, RunConfiguration, IPrerequisite
from .controller import PiperTrainingController
from .settings import PiperTrainingSettings
from .container.settings import TrainingSettings
from .model import PiperTrainingModel
from pathlib import Path
import zipfile
import os
import shutil
import re

class Monitor:
    def __init__(self, api: 'PiperTraining', expected_epochs, folder_name: str):
        self.api = api
        self.expected_epochs = expected_epochs
        self.first_epoch = None
        self.folder_name = folder_name

    def __call__(self, s:str):
        print(s)
        epochs = re.findall(self.folder_name+'/epoch=(\d+)-step', s)
        if len(epochs) > 0:
            try:
                ep = int(epochs[-1])
                if self.first_epoch is None:
                    self.first_epoch = ep
                    return
                percentage = (ep-self.first_epoch)/(self.expected_epochs-self.first_epoch)
                self.api.context.logger.report_progress(percentage)
            except:
                pass



class PiperTraining(OnDemandDockerApi[PiperTrainingSettings, PiperTrainingController]):
    def _unzip_dataset(self, name: str, path: Path, enable_recreate):
        csv = []
        trainings_folder = self.controller.resource_folder('trainings')
        dataset_folder = trainings_folder/name/'source'
        if dataset_folder.is_dir() and not enable_recreate:
            raise ValueError(f"Folder for training {name} exists")
        shutil.rmtree(dataset_folder, ignore_errors=True)
        os.makedirs(dataset_folder/'wav')
        with zipfile.ZipFile(path, 'r') as file:
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
        single_speaker = len(set(c['character'] for c in csv)) == 1
        with open(dataset_folder / 'metadata.csv', 'w') as file:
            for record in csv:
                if single_speaker:
                    file.write(f'{record["id"]}|{record["text"]}\n')
                else:
                    file.write(f'{record["id"]}|{record["character"]}|{record["text"]}\n')



    def train(self, name: str, dataset: FileLike.Type, settings: TrainingSettings|dict|None = None, reset_if_existing: bool = False):
        if settings is None:
            settings = TrainingSettings()
        elif isinstance(settings, dict):
            settings = TrainingSettings(**settings)

        path = FileLike(dataset, self.cache_folder).get_path()
        if not settings.continue_existing:
            self._unzip_dataset(name, path, reset_if_existing)
        FileIO.write_json(settings.__dict__, self.controller.resource_folder('trainings', name)/'settings.json')

        configuration = RunConfiguration(
            detach_and_interactive=False,
            mount_top_resource_folder=True,
            command_line_arguments=['--dataset',name]
        )

        max_epochs = settings.max_epochs
        monitor = Monitor(self, max_epochs, 'checkpoints')
        self.controller.run_with_configuration(configuration, monitor)


    def export(self, name: str, max_epochs: int, cleanup: bool = False):
        result = []
        configuration = RunConfiguration(
            detach_and_interactive=False,
            mount_top_resource_folder=True,
            command_line_arguments=['--dataset', name, '--export']
        )
        monitor = Monitor(self, max_epochs, 'result')
        self.controller.run_with_configuration(configuration, monitor)
        result_folder = self.controller.resource_folder('trainings',name,'result')
        for file in os.listdir(result_folder):
            dst_filename = self.current_job_id+'_'+file
            shutil.copy(
                result_folder/file,
                self.cache_folder/dst_filename,
            )
            if file.endswith('.onnx'):
                result.append(dict(onnx=dst_filename, json=dst_filename+'.json'))

        if cleanup:
            shutil.rmtree(self.controller.resource_folder('trainings', name))

        return result

    @staticmethod
    def create_training_pack(
            dataset: FileLike.Type,
            settings: TrainingSettings|dict|None = None,
            custom_name: str|None = None,
            clean_up_afterwards: bool = False,
            reset_if_existing: bool = False
    ):
        name = custom_name if custom_name is not None else FileLike.get_name(dataset, True).split('.')[0]

        from brainbox import BrainBox
        training_task: BrainBox.Task = BrainBox.Task.call(PiperTraining).train(name, dataset, settings, reset_if_existing).to_task()
        id = training_task.id
        training_task.batch = id

        export_task: BrainBox.Task = BrainBox.Task.call(PiperTraining).export(name, settings.max_epochs, clean_up_afterwards).to_task()
        export_task.dependencies['*training'] = id
        export_task.batch = id

        return BrainBox.CombinedTask(
            export_task,
            (training_task,)
        )







    Controller = PiperTrainingController
    Settings = PiperTrainingSettings
    TrainingSettings = TrainingSettings
    Model = PiperTrainingModel
