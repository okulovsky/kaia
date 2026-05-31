import json
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

from foundation_kaia.brainbox_utils import LongBrainboxProcess, logger, subprocess_streaming_call
from interface import CheckpointInfo, OneTrainerParameters

EPOCH_RE = re.compile(r'epoch:\s+(\d+)%')
SAVE_FILE_RE = re.compile(r'-save-(\d+)-(\d+)-(\d+)')


class Loc:
    @staticmethod
    def training_root(training_id: str) -> Path:
        return Path(f'/resources/training/{training_id}')

    @staticmethod
    def images_dir(training_id: str) -> Path:
        return Loc.training_root(training_id) / 'images'

    @staticmethod
    def config_path(training_id: str) -> Path:
        return Loc.training_root(training_id) / 'config.json'

    @staticmethod
    def output_dir(training_id: str) -> Path:
        return Loc.training_root(training_id) / 'output'

    @staticmethod
    def save_dir(training_id: str) -> Path:
        return Loc.output_dir(training_id) / 'workspace' / 'save'


class Training(LongBrainboxProcess[list[CheckpointInfo]]):
    def __init__(self, training_id: str, parameters: OneTrainerParameters, config: Any):
        self.training_id = training_id
        self.parameters = parameters
        self.config = config

    def unzip_dataset(self) -> int:
        images_dir = Loc.images_dir(self.training_id)
        shutil.rmtree(images_dir, ignore_errors=True)
        images_dir.mkdir(parents=True)
        with zipfile.ZipFile(Loc.training_root(self.training_id) / 'dataset.zip', 'r') as zf:
            zf.extractall(images_dir)
        return len(list(images_dir.glob('*.txt')))

    def create_config(self, image_count: int) -> None:
        if isinstance(self.config, str):
            base = json.loads(Path(f'/home/app/main/configs/{self.config}.json').read_text())
        else:
            base = dict(self.config)

        p = self.parameters
        output_dir = Loc.output_dir(self.training_id)
        images_dir = Loc.images_dir(self.training_id)

        base['workspace_dir'] = str(output_dir / 'workspace')
        base['cache_dir'] = str(output_dir / 'cache')
        base['base_model_name'] = f'/base_models/{p.base_model}'
        base['output_model_destination'] = str(output_dir / f'{p.name}.safetensors')
        base['batch_size'] = p.batch_size
        base['epochs'] = int(p.target_steps / (image_count / p.batch_size)) + 1

        if p.save_every_n_steps is not None:
            base['save_every'] = p.save_every_n_steps


        base['concepts'][0]['name'] = p.name
        base['concepts'][0]['path'] = str(images_dir)

        base['samples'] = [
            {'enabled': True, 'prompt': prompt,
             'negative_prompt': p.negatives or '', 'width': 1024, 'height': 1024}
            for prompt in p.prompts
        ]

        Loc.config_path(self.training_id).write_text(json.dumps(base, indent=2))
        return base

    def run_training(self) -> None:
        for line in subprocess_streaming_call(
            ['python3', '/home/app/repo/scripts/train.py',
             '--config-path', str(Loc.config_path(self.training_id))],
            cwd='/home/app/repo',
            env={**os.environ, 'PYTHONUNBUFFERED': '1'},
        ):
            logger.info(line)
            m = EPOCH_RE.search(line)
            if m:
                logger.progress(int(m.group(1)) / 100.0)

    def collect_checkpoints(self, total_epochs, total_steps) -> list[CheckpointInfo]:
        result = []

        save_dir = Loc.save_dir(self.training_id)
        if save_dir.exists():
            for path in sorted(save_dir.glob('*.safetensors')):
                m = SAVE_FILE_RE.search(path.stem)
                epoch = int(m.group(2)) if m else 0
                step = int(m.group(1)) if m else 0
                result.append(CheckpointInfo(
                    training_id=self.training_id,
                    filename=path.name,
                    step = step,
                    epoch=epoch,
                    is_final=False,
                ))

        output_dir = Loc.output_dir(self.training_id)
        for path in sorted(output_dir.glob('*.safetensors')):
            result.append(CheckpointInfo(
                training_id=self.training_id,
                filename=path.name,
                epoch=total_epochs,
                step=total_steps,
                is_final=True,
            ))

        return result

    def execute(self) -> list[CheckpointInfo]:
        logger.info('Unpacking dataset')
        image_count = self.unzip_dataset()

        logger.info(f'Creating config ({image_count} caption files found)')
        Loc.output_dir(self.training_id).mkdir(parents=True, exist_ok=True)
        cfg = self.create_config(image_count)

        with logger.section('Training'):
            self.run_training()

        return self.collect_checkpoints(cfg['epochs'], self.parameters.target_steps)
