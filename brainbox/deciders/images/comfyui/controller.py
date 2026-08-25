from pathlib import Path
from typing import Iterable

from ....framework import (
    BrainboxImageBuilder, IImageBuilder, RunConfiguration,
    DockerMarshallingController, SelfTestCase,
)
from .settings import ComfyUISettings
from .workflows import Upscale, TextToImage


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
                "RUN printf 'N\\nY' | comfy install --nvidia --cuda-version 13.0 --version 0.31.0",
            ),
        )

    def get_service_run_configuration(self, port: int, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f'`parameter` must be None for {self.get_name()}')
        publish_ports = {port: 8080}
        if self.context.instance_registry.count_instances(self.get_name()) == 0:
            publish_ports[8188] = 8188
        return RunConfiguration(
            publish_ports=publish_ports,
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

    def get_loading_time_in_seconds(self) -> int:
        return 120

    def create_api(self, base_url: str):
        from .api import ComfyUIApi
        return ComfyUIApi(base_url)

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        yield SelfTestCase(
            Upscale(Path(__file__).parent/"image.png"),
            title="Upscaling",
            file_type=SelfTestCase.FileType.Image,
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
            title="Text to image",
            file_type=SelfTestCase.FileType.Image,
        )
