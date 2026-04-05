from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder, DockerMarshallingController,
    BrainBoxApi, BrainBoxTask, File
)
from ...common import VOICEOVER_TEXT
from .settings import CosyVoiceSettings
from pathlib import Path
from .app.model import CosyVoiceInstaller


class CosyVoiceController(DockerMarshallingController[CosyVoiceSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.10.18',
            #allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies(
                    '2.7.0', 'cu128', True
                ),
                BrainboxImageBuilder.CustomDependencies(('numpy', 'cython')),
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies()
            ),
            repository=BrainboxImageBuilder.Repository(
                'https://github.com/FunAudioLLM/CosyVoice',
                '1dcc59676fe3fa863f983ab7820e481560c73be7',
                install=False,
                recursive_clone=True
            ),
            keep_dockerfile=True
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            dont_rm=False
        )

    def get_installer(self) -> Installer|None:
        return CosyVoiceInstaller(self.resource_folder())

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return CosyVoiceSettings()

    def create_api(self):
        from .api import CosyVoiceApi
        return CosyVoiceApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import CosyVoice

        yield SelfTestCase(
            CosyVoice.new_task().train(
                'lina',
                "One little spark, and before you know it, the whole world is burning.",
                File.read(Path(__file__).parent / 'lina.wav')
            ),
            None
        )
        yield SelfTestCase(
            CosyVoice.new_task().voice_to_text('lina', VOICEOVER_TEXT),
            SelfTestCase.assertFileIsSound()
        )

        yield SelfTestCase(
            CosyVoice.new_task().voice_to_text_translingual('lina', "Ein einziger Funke, und unmerklich gerät die Welt in Brand."),
            SelfTestCase.assertFileIsSound()
        )
        yield SelfTestCase(
            CosyVoice.new_task().voice_to_file('lina', File.read(Path(__file__).parent / 'lina_ru.wav')),
            SelfTestCase.assertFileIsSound()
        )
