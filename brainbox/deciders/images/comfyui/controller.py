from pathlib import Path
from typing import Iterable

from ....framework import (
    BrainboxImageBuilder, IImageBuilder, RunConfiguration,
    DockerMarshallingController, SelfTestCase,
)
from .settings import ComfyUISettings
from .workflows import Upscale, TextToImage


def _is_image(result, api, test_case):
    from PIL import Image
    from io import BytesIO
    bts = api.cache.read(result)
    img = Image.open(BytesIO(bts))
    test_case.assertGreater(img.width, 0)
    test_case.assertGreater(img.height, 0)

class ComfyUIController(DockerMarshallingController[ComfyUISettings]):
    def get_image_builder(self) -> IImageBuilder:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            apt_install=('curl',),
            dependencies=(
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
            finishing_installation_steps=(
                "RUN printf 'N\\nY' | comfy install --nvidia --cuda-version 13.0",
            ),
        )

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f'`parameter` must be None for {self.get_name()}')
        return RunConfiguration(
            publish_ports={
                self.connection_settings.port: 8080,
                8188: 8188,
            },
            mount_custom_folders={
                str(self.resource_folder('models')):       '/home/app/comfy/ComfyUI/models',
                str(self.resource_folder('input')):        '/home/app/comfy/ComfyUI/input',
                str(self.resource_folder('output')):       '/home/app/comfy/ComfyUI/output',
                str(self.resource_folder('custom_nodes')): '/home/app/comfy/ComfyUI/custom_nodes',
            },
            dont_rm=True
        )

    def get_installer(self):
        from .app.model import ComfyUIInstaller
        return ComfyUIInstaller(self.resource_folder())

    def get_default_settings(self):
        return ComfyUISettings()

    def create_api(self):
        from .api import ComfyUIApi
        return ComfyUIApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        yield SelfTestCase(
            Upscale(Path(__file__).parent/"image.png"),
            _is_image,
            "Upscaling"
        )
        checkpoint = next(
            inst.model.get_name()
            for inst in self.settings.models_to_install
            if inst.model is not None and inst.model.models_subfolder == 'checkpoints'
        )
        yield SelfTestCase(
            TextToImage(
                prompt='a cat sitting on a windowsill',
                negative_prompt='blurry, ugly, low quality',
                model=checkpoint,
            ),
            _is_image,
            "Text to image",
        )
