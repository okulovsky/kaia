from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder, DockerMarshallingController
)
from ...common import VOICEOVER_TEXT
from .settings import ParlerTtsSettings
from pathlib import Path
from .app.model import ParlerTtsInstaller


class ParlerTtsController(DockerMarshallingController[ParlerTtsSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('ffmpeg',),
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies(
                    '2.7.0', 'cu128', True
                ),
                BrainboxImageBuilder.CustomDependencies(
                    ('numpy==1.26.4',)
                ),
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies()
            ),
            repository=BrainboxImageBuilder.Repository(
                'https://github.com/huggingface/parler-tts',
                'd108732cd57788ec86bc857d99a6cabd66663d68',
                pip_install_options='--no-deps -e',
            ),
            keep_dockerfile=True
        )

    def get_installer(self) -> Installer | None:
        return ParlerTtsInstaller(self.resource_folder())

    def get_service_run_configuration(self, port: int, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={port: 8080},
        )

    def get_notebook_configuration(self) -> RunConfiguration | None:
        return self.get_service_run_configuration(0, None).as_notebook_service()

    def get_default_settings(self):
        return ParlerTtsSettings()

    def get_loading_time_in_seconds(self) -> int:
        return 180

    def create_api(self, base_url: str):
        from .api import ParlerTtsApi
        return ParlerTtsApi(base_url)

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import ParlerTts
        description = ParlerTts.Speakers.description('Jon')
        yield SelfTestCase(ParlerTts.new_task().train('test_speaker', description), None)
        yield SelfTestCase(
            ParlerTts.new_task().voiceover(VOICEOVER_TEXT, 'test_speaker'),
            file_type=SelfTestCase.FileType.Sound
        )
        unnamed_description = (
            "A female speaker delivers a slightly expressive and animated speech with a moderate "
            "speed and pitch. The recording is of very high quality, with the speaker's voice "
            "sounding clear and very close up."
        )
        yield SelfTestCase(
            ParlerTts.new_task().voiceover_with_description(VOICEOVER_TEXT, unnamed_description),
            file_type=SelfTestCase.FileType.Sound
        )
        for seed in (42, 12345):
            yield SelfTestCase(
                ParlerTts.new_task().voiceover_with_description(VOICEOVER_TEXT, unnamed_description, seed=seed),
                title=f'The same description with seed={seed}: the seed picks the random voice',
                file_type=SelfTestCase.FileType.Sound
            )
