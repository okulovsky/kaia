import datetime
import os
import shutil
import time
import zipfile


from pathlib import Path
from ....framework import FileLike, OnDemandDockerApi, FileIO, Loc
from .settings import KohyaSSSettings
from .controller import KohyaSSController
from dataclasses import dataclass
import toml
import subprocess
import re
from enum import Enum
from .exporter import LorasExporter



@dataclass
class LoraTrainingSettings:
    class TrainingType:
        sdxl = 'sdxl_train_network.py'

    character_name: str
    class_name: str
    repeat_count: int = 10
    kohya_ss_executable: str = TrainingType.sdxl
    base_model_name: str = "sdXL_v10VAEFix.safetensors"
    prompt: str|None = None
    mock_training: bool = False
    regularization_repeat_count: int|None = None




class KohyaSS(OnDemandDockerApi[KohyaSSSettings, KohyaSSController]):
    def __init__(self):
        pass

    def _get_dst_folder(self):
        return self.controller.resource_folder('training',self.training_id)

    def _unzip(self, zip_file: FileLike.Type, folder: Path, tmp_file_name: Path):
        with FileLike(zip_file, self.cache_folder) as file:
            FileIO.write_bytes(file.read(), tmp_file_name)
        os.makedirs(folder, exist_ok=True)
        with zipfile.ZipFile(tmp_file_name, 'r') as zip_file:
            for file_name in zip_file.namelist():
                content = zip_file.read(file_name)
                FileIO.write_bytes(
                    content,
                    folder/file_name,
                )
        os.unlink(tmp_file_name)

    def _unzip_dataset(self,
                       dataset_zip_file: FileLike.Type,
                       settings: LoraTrainingSettings
                       ):
        dst = self._get_dst_folder()
        os.makedirs(dst, exist_ok=True)
        image_path = (
                dst
                /'img'
                /f'{settings.repeat_count}_{settings.character_name} {settings.class_name}'
        )
        self._unzip(dataset_zip_file, image_path, dst/'dataset.zip')


    def _unzip_regularization(self,
                              regularization_zip_file: FileLike.Type,
                              settings: LoraTrainingSettings
                              ):
        dst = self._get_dst_folder()
        os.makedirs(dst, exist_ok=True)
        regularization_path = (
            dst
            /'reg'
            /f'{settings.regularization_repeat_count}_{settings.class_name}'
        )
        self._unzip(regularization_zip_file, regularization_path, dst/'regularization.zip')


    def _fix_and_write_toml_file(self, cfg, settings: LoraTrainingSettings, job_id):
        training_path = '/app/training/'+self.training_id+'/'
        models_path = '/app/models/'

        cfg['logging_dir'] = training_path+'log'
        cfg['output_dir'] = training_path+'model'
        cfg['sample_prompts'] = training_path+'model/prompt.txt'
        cfg['train_data_dir'] = training_path+'img'
        cfg['pretrained_model_name_or_path'] = models_path+settings.base_model_name
        cfg['output_name'] = job_id

        if settings.regularization_repeat_count is not None:
            cfg['reg_data_dir'] = training_path+'reg'

        model_folder = self._get_dst_folder()/'model'
        os.makedirs(model_folder, exist_ok=True)
        with open(model_folder/'config.toml', 'w', encoding='utf-8') as file:
            toml.dump(cfg, file)

    def _small_files_and_folders(self, settings: LoraTrainingSettings):
        text = settings.character_name + ", " + settings.class_name
        if settings.prompt is not None:
            text = settings.prompt
        dst_folder = self._get_dst_folder()
        FileIO.write_text(
            text,
            dst_folder / 'model/prompt.txt'
        )
        os.makedirs(dst_folder / 'log', exist_ok=True)

    def _dump_command_line_arguments(self, settings: LoraTrainingSettings):
        arguments = [
            '/home/1000/.local/bin/accelerate',
            'launch',
            '--dynamo_backend',
            'no',
            '--dynamo_mode',
            'default',
            '--mixed_precision',
            'fp16',
            '--num_processes',
            '1',
            '--num_machines',
            '1',
            '--num_cpu_threads_per_process',
            '2',
            f'/app/sd-scripts/{settings.kohya_ss_executable}',
            '--config_file',
            f'/app/training/{self.training_id}/model/config.toml'
        ]
        FileIO.write_json(arguments, self._get_dst_folder()/'parameters.json')


    def _get_logs_file_name(self):
        return  f'{self.training_id}.logs.txt'

    def _monitor(self, s):
        all_percentages = re.findall('steps: +(\d+)%', s)
        if len(all_percentages) > 0:
            try:
                value = int(all_percentages[-1]) / 100
            except:
                value = None
                pass
            self.context.logger.report_progress(value)
        with open(self.cache_folder/self._get_logs_file_name(), 'a', encoding='utf-8') as stream:
            stream.write(s)


    def run_lora_training(self,
                          dataset_zip_file: FileLike.Type,
                          toml_file_content: dict,
                          lora_training_settings: LoraTrainingSettings|dict,
                          regularization_zip_file: FileLike.Type|None = None,
                          description = None
                          ):
        if isinstance(lora_training_settings, dict):
            lora_training_settings = LoraTrainingSettings(**lora_training_settings)

        if (
                (lora_training_settings.regularization_repeat_count is None) !=
                (regularization_zip_file is None)
        ):
            raise ValueError("regularization_repeat_count must be set if and only if regularization_zip_file is provided")

        self.training_id = lora_training_settings.character_name + "_" + self.current_job_id

        dst_folder = self._get_dst_folder()
        shutil.rmtree(dst_folder, ignore_errors=True)

        self._unzip_dataset(dataset_zip_file, lora_training_settings)
        if regularization_zip_file is not None:
            self._unzip_regularization(regularization_zip_file, lora_training_settings)

        self._fix_and_write_toml_file(toml_file_content, lora_training_settings, self.training_id)
        self._small_files_and_folders(lora_training_settings)
        self._dump_command_line_arguments(lora_training_settings)

        config = self.controller.get_base_configuration()
        config.command_line_arguments = ['--train',self.training_id]
        if lora_training_settings.mock_training:
            config.command_line_arguments.append('--mock')
        self.run_container(config, self._monitor)

        error_code_file = dst_folder/'error_code.txt'
        if not error_code_file.is_file():
            raise ValueError(f"No error code was found. The container was probably forcibly removed. Logs are in {self._get_logs_file_name()}")
        error_code=FileIO.read_text(error_code_file)
        if error_code != '0':
            raise ValueError(f"Non-zero error code `{error_code}. Logs are in {self._get_logs_file_name()}")
        description['timestamp'] = str(datetime.datetime.now())
        return dict(
            training_id=self.training_id,
            log_file = self._get_logs_file_name(),
            training_folder = f'training/{self.training_id}',
            description = description,
        )


    Controller = KohyaSSController
    Settings = KohyaSSSettings
    Exporter = LorasExporter
    TrainingSettings = LoraTrainingSettings




