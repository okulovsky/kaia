import os
import shutil
import time
import zipfile

from .installer import KohyaSSInstaller
from pathlib import Path
from kaia.brainbox.deciders.arch.utils import FileLike
from dataclasses import dataclass
from kaia.brainbox.core import IApiDecider
from kaia.infra import FileIO, Loc
from kaia.brainbox.deployment import LocalExecutor
import toml
import subprocess
import re
from enum import Enum




@dataclass
class LoraTrainingSettings:
    class TrainingType(Enum):
        sdxl = 'sdxl_train_network.py'

    training_name: str
    character_name: str
    class_name: str
    repeat_count: int = 10
    kohya_ss_executable: 'LoraTrainingSettings.TrainingType' = TrainingType.sdxl
    base_model_name: str = "sdXL_v10VAEFix.safetensors"
    prompt: str|None = None
    mock_training: bool = False
    cleanup_afterwarsd: bool = True
    regularization_repeat_count: int|None = None
    output_subfolder: str|None = None




class KohyaSS(IApiDecider):
    def __init__(self, installer: KohyaSSInstaller):
        self.installer = installer


    def _get_dst_folder(self, settings: LoraTrainingSettings):
        return self.installer.resource_folder('training',settings.training_name)


    def _unzip(self, zip_file: FileLike.Type, folder: Path, tmp_file_name: Path):
        with FileLike(zip_file, self.file_cache) as file:
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
        dst = self._get_dst_folder(settings)
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
        dst = self._get_dst_folder(settings)
        os.makedirs(dst, exist_ok=True)
        regularization_path = (
            dst
            /'reg'
            /f'{settings.regularization_repeat_count}_{settings.class_name}'
        )
        self._unzip(regularization_zip_file, regularization_path, dst/'regularization.zip')


    def _fix_and_write_toml_file(self, cfg, settings: LoraTrainingSettings, job_id):
        training_path = '/app/training/'+settings.training_name+'/'
        models_path = '/app/models/'

        cfg['logging_dir'] = training_path+'log'
        cfg['output_dir'] = training_path+'model'
        cfg['sample_prompts'] = training_path+'model/prompt.txt'
        cfg['train_data_dir'] = training_path+'img'
        cfg['pretrained_model_name_or_path'] = models_path+settings.base_model_name
        cfg['output_name'] = job_id

        if settings.regularization_repeat_count is not None:
            cfg['reg_data_dir'] = training_path+'reg'

        model_folder = self._get_dst_folder(settings)/'model'
        os.makedirs(model_folder, exist_ok=True)
        with open(model_folder/'config.toml', 'w') as file:
            toml.dump(cfg, file)

    def _small_files_and_folders(self, settings: LoraTrainingSettings):
        text = settings.character_name + ", " + settings.class_name
        if settings.prompt is not None:
            text = settings.prompt
        dst_folder = self._get_dst_folder(settings)
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
            f'/app/sd-scripts/{settings.kohya_ss_executable.value}',
            '--config_file',
            f'/app/training/{settings.training_name}/model/config.toml'
        ]
        FileIO.write_json(arguments, self._get_dst_folder(settings)/'parameters.json')


    def run_lora_training(self,
                          dataset_zip_file: FileLike.Type,
                          toml_file_content: dict,
                          lora_training_settings: LoraTrainingSettings,
                          regularization_zip_file: FileLike.Type|None = None,
                          ):
        if (
                (lora_training_settings.regularization_repeat_count is None) !=
                (regularization_zip_file is None)
        ):
            raise ValueError("regularization_repeat_count must be set if and only if regularization_zip_file is provided")

        job_id =  lora_training_settings.training_name+"_"+self.current_job_id
        dst_folder = self._get_dst_folder(lora_training_settings)
        shutil.rmtree(dst_folder, ignore_errors=True)

        self._unzip_dataset(dataset_zip_file, lora_training_settings)
        if regularization_zip_file is not None:
            self._unzip_regularization(regularization_zip_file, lora_training_settings)

        self._fix_and_write_toml_file(toml_file_content, lora_training_settings, job_id)
        self._small_files_and_folders(lora_training_settings)
        self._dump_command_line_arguments(lora_training_settings)

        arguments = ['--train',lora_training_settings.training_name]
        if lora_training_settings.mock_training:
            arguments.append('--mock')
        worker = self.installer.main_service.as_service_worker(*arguments)
        worker._container_runner._detach = True
        worker.run()

        logs = None
        while True:
            time.sleep(1)
            containers = self.installer._image_source.get_relevant_containers(LocalExecutor())
            if len(containers) == 0:
                break

            try:
                logs = subprocess.check_output(['docker','logs',containers[0]], stderr=subprocess.STDOUT)
            except:
                continue

            logs = logs.decode('utf-8')
            all_percentages = re.findall('steps: +(\d+)%', logs)
            if len(all_percentages) > 0:
                try:
                    value = int(all_percentages[-1])/100
                except:
                    value = None
                    pass
                self.progress_reporter.report_progress(value)

        logs_file_name = f'{job_id}.logs.txt'
        FileIO.write_text(logs, self.file_cache/logs_file_name)
        error_code_file = dst_folder/'error_code.txt'
        if not error_code_file.is_file():
            raise ValueError(f"No error code was found. The container was probably forcibly removed. Logs are in {logs_file_name}")
        error_code=FileIO.read_text(error_code_file)
        if error_code != '0':
            raise ValueError(f"Non-zero error code `{error_code}. Logs are in {logs_file_name}")

        result = []
        model_folder = self._get_dst_folder(lora_training_settings)/'model'
        for file in os.listdir(model_folder):
            if file.startswith(job_id) and (model_folder/file).is_file() and file.endswith('.safetensors'):
                output_folder = self.installer.settings.loras_models_folder
                if output_folder is None:
                    output_folder = self.file_cache
                if lora_training_settings.output_subfolder is not None:
                    output_folder /= lora_training_settings.output_subfolder
                os.makedirs(output_folder, exist_ok=True)
                shutil.move(model_folder/file, output_folder/file)
                result.append(file)

        if lora_training_settings.cleanup_afterwarsd:
            shutil.rmtree(dst_folder, ignore_errors=True)

        return dict(files=result, logs=logs_file_name)







