from typing import Iterable
from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    RunConfiguration, SelfTestCase, IImageBuilder, BrainboxImageBuilder,
    DockerMarshallingController, File,
)
from .settings import WhisperKenLMSettings
from pathlib import Path
from .app.model import WhisperKenLMInstaller


class WhisperKenLMController(DockerMarshallingController[WhisperKenLMSettings]):
    def get_image_builder(self) -> IImageBuilder | None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.11.11',
            ('ffmpeg', 'build-essential', 'cmake', 'git',
             'libboost-program-options-dev', 'libboost-system-dev',
             'libboost-thread-dev', 'libboost-test-dev'),
            allow_arm64=True,
            custom_apt_installation=(
                'RUN git clone --depth 1 https://github.com/kpu/kenlm.git /tmp/kenlm'
                ' && cmake -S /tmp/kenlm -B /tmp/kenlm/build -DCMAKE_BUILD_TYPE=Release'
                ' && make -C /tmp/kenlm/build -j$(nproc) lmplz build_binary'
                ' && cp /tmp/kenlm/build/bin/lmplz /usr/local/bin/'
                ' && cp /tmp/kenlm/build/bin/build_binary /usr/local/bin/'
                ' && pip install /tmp/kenlm'
                ' && rm -rf /tmp/kenlm',
            ),
            dependencies=(
                BrainboxImageBuilder.PytorchDependencies('2.7.0', cuda_version=None),
                BrainboxImageBuilder.CustomDependencies(('transformers', 'soundfile')),
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
        )

    def get_installer(self) -> Installer | None:
        return WhisperKenLMInstaller(self.resource_folder())

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port: 8080},
            mount_resource_folders={
                'pretrained': '/home/app/.cache/huggingface',
            },
        )

    def get_default_settings(self):
        return WhisperKenLMSettings()

    def create_api(self):
        from .api import WhisperKenLMApi
        return WhisperKenLMApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import WhisperKenLM
        from ....framework import File
        file = File.read(Path(__file__).parent / 'files/test_voice.wav')
        yield SelfTestCase(
            WhisperKenLM.new_task().train_lm('one little spark\nbefore you know it\nthe whole world is burning'),
        )
        yield SelfTestCase(
            WhisperKenLM.new_task().transcribe(file),
            lambda result, api, tc: tc.assertGreater(len(result), 0),
        )
