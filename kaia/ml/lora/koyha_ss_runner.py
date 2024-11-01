import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from kaia.infra import FileIO
import shutil
import os
import toml
from .annotation_controller import AnnotationController



@dataclass
class KohyaSettings:
    dataset_path: Path
    kohya_ss_training_path: Path
    kohya_ss_installation_path: Path
    toml_config_path: Path
    character_name: str
    class_name: str
    repeat_count: int = 10
    kohya_ss_executable: str = 'sdxl_train_network.py'
    base_model_name_or_path: Path|str = "runwayml/stable-diffusion-v1-5"
    folder_with_ready_pictures = 'ready_images'
    prompt: str|None = None
    output_lora_folder: Path|None = None
    replace_upderscore_with_space: bool = True


class KohyaRunner:
    def __init__(self, settings: KohyaSettings):
        self.settings = settings

    def _export_images(self):
        image_path = (
                self.settings.kohya_ss_training_path /
                f'img/{self.settings.repeat_count}_{self.settings.character_name} {self.settings.class_name}'
        )
        os.makedirs(image_path,exist_ok=True)
        controller = AnnotationController(self.settings.dataset_path)
        for annotation in controller.annotations:
            if annotation.stored.skipped:
                continue
            if not annotation.stored.reviewed:
                continue
            original_file_name = annotation.status.source_path.name.split('.')[0]
            shutil.copyfile(
                annotation.status.upscaled_path,
                image_path/(original_file_name+'.png')
            )
            tags = [tag.name for tag in annotation.stored.tags if tag.status]
            tags += annotation.stored.new_tags
            tags = [t for t in tags if t not in annotation.settings.exclude_tags]
            tags += [self.settings.character_name]
            tags = ", ".join(tags)
            if self.settings.replace_upderscore_with_space:
                tags = tags.replace('_',' ')
            FileIO.write_text(tags, image_path/(original_file_name+'.txt'))

    def _fix_config_file(self):
        with open(self.settings.toml_config_path, 'r') as file:
            cfg = toml.load(file)

        cfg['logging_dir'] = str(self.settings.kohya_ss_training_path/'log')
        cfg['output_dir'] = str(self.settings.kohya_ss_training_path/'model')
        cfg['sample_prompts'] = str(self.settings.kohya_ss_training_path/'model/prompt.txt')
        cfg['train_data_dir'] = str(self.settings.kohya_ss_training_path/'img')
        cfg['pretrained_model_name_or_path'] = str(self.settings.base_model_name_or_path)

        return cfg


    def export(self, reset = False):
        if reset and self.settings.kohya_ss_training_path.is_dir():
            shutil.rmtree(self.settings.kohya_ss_training_path)
        os.makedirs(self.settings.kohya_ss_training_path)
        self._export_images()
        os.makedirs(self.settings.kohya_ss_training_path/'log')
        os.makedirs(self.settings.kohya_ss_training_path / 'model')
        config = self._fix_config_file()
        with open(self.settings.kohya_ss_training_path/'model/config.toml', 'w') as file:
            toml.dump(config, file)
        text = self.settings.character_name+", "+self.settings.class_name
        if self.settings.prompt is not None:
            text = self.settings.prompt
        FileIO.write_text(
            text,
            self.settings.kohya_ss_training_path/'model/prompt.txt'
        )


    def produce_command_line_command(self):
        return [
            str(self.settings.kohya_ss_installation_path/'venv/bin/accelerate'),
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
            str(self.settings.kohya_ss_installation_path/f'sd-scripts/{self.settings.kohya_ss_executable}'),
            '--config_file',
            str(self.settings.kohya_ss_training_path/'model/config.toml')
        ]

    def copy_models(self, suffix: str|None=None):
        if self.settings.output_lora_folder is None:
            raise ValueError("Output LORA folder is not set (must be inside your Automatic1111 data folder")

        if suffix is not None:
            suffix='-'+suffix
        else:
            suffix=''

        for file in os.listdir(self.settings.kohya_ss_training_path/'model'):
            print(file)
            match = re.match('^last(.*)\.safetensors$', file)
            if match:
                proper_suffix = match.group(1)
                dst_name = f'{self.settings.character_name}{suffix}{proper_suffix}.safetensors'
                print(file, dst_name)
                shutil.copyfile(
                    self.settings.kohya_ss_training_path/'model'/file,
                    Path(self.settings.output_lora_folder)/dst_name
                )
