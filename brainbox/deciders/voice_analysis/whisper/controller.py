from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    File, RunConfiguration, SelfTestCase, IImageBuilder, BrainboxImageBuilder,
    DockerMarshallingController, BrainBoxApi, BrainBoxTask,
)
from .settings import WhisperSettings
from pathlib import Path
from .app.model import WhisperInstaller


class WhisperController(DockerMarshallingController[WhisperSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('ffmpeg',),
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies(
                    '2.7.0', 'cu128', True
                ),
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies()
            )
        )

    def get_installer(self) -> Installer | None:
        return WhisperInstaller(self.resource_folder())

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            None,
            publish_ports={self.connection_settings.port: 8080},
        )

    def get_default_settings(self):
        return WhisperSettings()

    def create_api(self):
        from .api import WhisperApi
        return WhisperApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Whisper
        file = File.read(Path(__file__).parent / 'files/test_voice.wav')
        expected = 'One little spark and before you know it, the whole world is burning.'
        for model in self.settings.models_to_install:
            yield SelfTestCase(
                Whisper.new_task().transcribe(file, model),
                lambda result, api, tc: tc.assertEqual(expected, result['text'].strip())
            )
            yield SelfTestCase(
                Whisper.new_task().transcribe_text(file, model),
                SelfTestCase.assertEqual(expected)
            )
