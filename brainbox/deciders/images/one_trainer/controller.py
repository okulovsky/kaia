import io
import json
import zipfile
from pathlib import Path
from unittest import TestCase

from foundation_kaia.marshalling import TypeTools

from ....framework import (
    BrainboxImageBuilder, IImageBuilder, RunConfiguration,
    DockerMarshallingController, BrainBoxApi,
)
from .settings import OneTrainerSettings
from .app.interface import CheckpointInfo


class OneTrainerController(DockerMarshallingController[OneTrainerSettings]):
    def get_image_builder(self) -> IImageBuilder:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            apt_install=('git', 'libgl1-mesa-glx', 'libglib2.0-0'),
            custom_apt_installation=(
                "RUN ln -sf /home/app/.local/bin/tensorboard /usr/local/bin/tensorboard",
            ),
            repository=BrainboxImageBuilder.Repository(
                url='https://github.com/Nerogar/OneTrainer',
                commit='423c3b3',
                install=False,
                remove_repo=False,
                post_install_commands=(
                    'pip install --user -r /home/app/repo/requirements-global.txt',
                ),
            ),
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies('2.9.1', 'cu128', torchvideo_version='0.24.1'),
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
            keep_dockerfile=True,
        )

    def get_default_settings(self):
        return OneTrainerSettings()

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
            mount_custom_folders={
                str(self.resource_folder().parent / 'ComfyUI' / 'models' / 'checkpoints'): '/base_models',
            },
        )

    def create_api(self):
        from .api import OneTrainerApi
        return OneTrainerApi()

    def custom_self_test(self, api: BrainBoxApi, tc: TestCase):
        from .api import OneTrainer
        from ..comfyui import ComfyUI
        from ..comfyui.workflows import TextToImage
        from PIL import Image, ImageDraw

        TRAINING_ID = 'one_trainer_self_test'
        LORA_NAME = 'one_trainer_self_test.safetensors'
        BASE_MODEL = 'ponyDiffusionV6XL_v6StartWithThisOne.safetensors'
        COLORS = {'red': (255, 0, 0), 'blue': (0, 0, 255), 'green': (0, 128, 0)}

        # Build test dataset: 5 images per colour, each with a paired .txt caption
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            for color_name, rgb in COLORS.items():
                for i in range(5):
                    img = Image.new('RGB', (512, 512), (200, 200, 200))
                    ImageDraw.Draw(img).rectangle([100, 100, 400, 400], fill=rgb)
                    img_buf = io.BytesIO()
                    img.save(img_buf, format='PNG')
                    zf.writestr(f'{color_name}_{i}.png', img_buf.getvalue())
                    zf.writestr(f'{color_name}_{i}.txt', f'{color_name} rectangle')
        buf.seek(0)

        # Run training
        task = OneTrainer.new_task().train(
            TRAINING_ID,
            OneTrainer.Parameters(
                name='self_test_lora',
                base_model=BASE_MODEL,
                prompts=['red rectangle', 'blue rectangle'],
                target_steps=50,
                batch_size=2,
                save_every_n_steps=10
            ),
            buf,
        )
        job_id = None
        try:
            job_id = api.add(task)
            log_file = api.join(job_id)
        except Exception:
            if job_id is not None:
                from pprint import pprint
                pprint(api.jobs.get_job(job_id).log)
            raise

        # Parse streaming JSON-line log to find the final checkpoint list
        checkpoints_result = None
        for line in api.cache.read_file(log_file).string_content.split('\n'):
            if not line.strip():
                continue
            try:
                js = json.loads(line)
                if js.get('result') is not None:
                    checkpoints_result = TypeTools.deserialize(js['result'], list[CheckpointInfo])
            except Exception:
                pass

        print(checkpoints_result)
        tc.assertIsNotNone(checkpoints_result, 'No checkpoint result found in training log')
        tc.assertGreater(len(checkpoints_result), 0, 'Training produced no checkpoint files')

        # Upload the final checkpoint to ComfyUI as a LoRA
        final = [c for c in checkpoints_result if c.is_final]
        tc.assertGreater(len(final), 0, 'Training produced no final checkpoint')
        ckpt = final[-1]
        ckpt_path = self.resource_folder('training', TRAINING_ID, 'output') / ckpt.filename
        api.resources(ComfyUI).upload(f'models/loras/{LORA_NAME}', ckpt_path)

        # Generate a sample image with ComfyUI using the trained LoRA
        result = api.execute(TextToImage(
                    prompt='red rectangle',
                    negative_prompt='',
                    model=BASE_MODEL,
                    lora_01=LORA_NAME,
                    strength_01=0.8,
                    width=512,
                    height=512,
                ))
        img = Image.open(io.BytesIO(api.cache.read(result)))
        tc.assertGreater(img.width, 0)
        tc.assertGreater(img.height, 0)

        # Cleanup
        api.resources(ComfyUI).delete(f'models/loras/{LORA_NAME}')
        api.execute(OneTrainer.new_task().delete(TRAINING_ID))
