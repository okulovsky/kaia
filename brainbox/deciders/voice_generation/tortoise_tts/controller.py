from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, File, INotebookableController
)
from ...common import VOICEOVER_TEXT, check_if_its_sound
from .settings import TortoiseTTSSettings
from pathlib import Path


class TortoiseTTSController(DockerWebServiceController[TortoiseTTSSettings], INotebookableController):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.9.21',
            repository=BrainboxImageBuilder.Repository(
                'https://github.com/neonbjb/tortoise-tts.git',
                '8a2563ecabe93c4fb626f876dd0c52c966edef2f',
                remove_files = ('setup.py',)
            ),
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port: 8084},
            mount_resource_folders=dict(
                voices='/home/app/repo/tortoise/voices/',
                hf_models='/home/app/.cache/huggingface/hub/',
                tortoise_models='/home/app/.cache/tortoise/models',
                stash='/stash',
            ),
        )

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return TortoiseTTSSettings()

    def create_api(self):
        from .api import TortoiseTTS
        return TortoiseTTS()

    def post_install(self):
        should_install = False
        for model in [
            self.resource_folder('hf_models')/'models--facebook--wav2vec2-large-960h',
            self.resource_folder('hf_models')/'models--jbetker--tacotron-symbols',
            self.resource_folder('hf_models')/'models--jbetker--wav2vec2-large-robust-ft-libritts-voxpopuli',
            self.resource_folder('tortoise_models') /'models--Manmay--tortoise-tts'
        ]:
            if not model.is_dir():
                should_install = True
                break
        if should_install:
            self.run_auxiliary_configuration(self.get_service_run_configuration(None).as_service_worker('--install'))


    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import TortoiseTTS

        TortoiseTTS.export_voice('test_voice', [Path(__file__).parent/'test_voice.wav']).execute(api)
        text = VOICEOVER_TEXT
        files = api.execute(BrainBoxTask.call(TortoiseTTS).dub(text=text, voice='test_voice'))
        yield TestReport.last_call(api).href('voiceover').result_is_array_of_files(File.Kind.Audio).with_comment("Voiceover")
        for i, fname in enumerate(files):
            file = api.open_file(fname)
            check_if_its_sound(file.content, tc)


