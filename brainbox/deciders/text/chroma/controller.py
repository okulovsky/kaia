from typing import Iterable
from pathlib import Path

from ....framework import (
    RunConfiguration, SelfTestCase, BrainboxImageBuilder, IImageBuilder,
    DockerMarshallingController,
)
from .settings import ChromaSettings
from .app.model import ChromaInstaller


class ChromaController(DockerMarshallingController[ChromaSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            allow_arm64=True,
            dependencies=(
                BrainboxImageBuilder.RequirementsLockTxt(),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
        )

    def get_installer(self):
        return ChromaInstaller(self.resource_folder())

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
            mount_resource_folders={
                'chroma': '/chroma',
                'models': '/home/app/fastembed_cache',
            },
        )

    def get_default_settings(self):
        return ChromaSettings()

    def create_api(self):
        from .api import ChromaApi
        return ChromaApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Chroma
        utterances = [
            {'text': 'set timer for 5 minutes', 'intent': 'set_timer', 'language': 'en'},
            {'text': 'cancel the timer please', 'intent': 'cancel_timer', 'language': 'en'},
            {'text': 'how much time is left', 'intent': 'time_left', 'language': 'en'},
        ]
        yield SelfTestCase(Chroma.new_task().train(utterances), None)
        yield SelfTestCase(
            Chroma.new_task().find_neighbors('please set a timer for 5 minutes', k=1),
            lambda result, api, tc: tc.assertEqual('set_timer', result[0]['intent']),
        )
        yield SelfTestCase(
            Chroma.new_task().get_vector('hello world'),
            lambda result, api, tc: tc.assertEqual(384, len(result)),
        )
