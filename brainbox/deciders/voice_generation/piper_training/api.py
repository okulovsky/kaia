from brainbox.framework import OnDemandDockerApi, FileLike, FileIO, File, RunConfiguration
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
    def __init__(self, api: 'PiperTraining', expected_epochs):
        self.api = api
        self.expected_epochs = expected_epochs
        self.first_epoch = None

    def __call__(self, s: str):
        print(s)
        epochs = re.findall('checkpoints/epoch=(\d+)-step', s)
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
    def _unzip_dataset(self, name: str, path: Path):
        csv = []
        dataset_folder = self.controller.resource_folder('trainings', name, 'source')
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



    def execute(self, dataset: FileLike.Type, settings: TrainingSettings|dict|None = None, name: str|None = None):
        if name is None:
            name = FileLike.get_name(dataset).split('.')[0]
        if settings is None:
            settings = {}
        elif isinstance(settings, TrainingSettings):
            settings = settings.__dict__

        path = FileLike(dataset, self.cache_folder).get_path()
        self._unzip_dataset(name, path)
        FileIO.write_json(settings, self.controller.resource_folder('trainings', name)/'settings.json')

        configuration = RunConfiguration(
            detach_and_interactive=False,
            mount_top_resource_folder=True,
            command_line_arguments=['--dataset',name]
        )

        monitor = Monitor(self, settings['max_epochs'])
        self.controller.run_with_configuration(configuration, monitor)
        result = []
        result_folder = self.controller.resource_folder('trainings',name,'result')
        for file in os.listdir(result_folder):
            dst_filename = self.current_job_id+'_'+file
            shutil.copy(
                result_folder/file,
                self.cache_folder/dst_filename,
            )
            if file.endswith('.onnx'):
                result.append(dst_filename)
        if settings['delete_training_files']:
            shutil.rmtree(self.controller.resource_folder('trainings', name))
        return result

    def convert_model(self, ckpt_model: FileLike.Type):
        name = FileLike.get_name(ckpt_model)

        with FileLike(ckpt_model, self.cache_folder) as stream:
            with open(self.controller.resource_folder('conversions')/name, 'wb') as output:
                output.write(stream.read())

        configuration = RunConfiguration(
            detach_and_interactive=False,
            mount_top_resource_folder=True,
            command_line_arguments=['--convert',str(name)]
        )
        self.controller.run_with_configuration(configuration, print)




    Controller = PiperTrainingController
    Settings = PiperTrainingSettings
    TrainingSettings = TrainingSettings
    Model = PiperTrainingModel
