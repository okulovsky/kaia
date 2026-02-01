from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, IModelDownloadingController, DownloadableModel,
    File
)
from ...common import VOICEOVER_TEXT, check_if_its_sound
from .settings import CosyVoiceSettings
from pathlib import Path


class CosyVoiceController(
    DockerWebServiceController[CosyVoiceSettings],
    INotebookableController,
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.10.18',
            #allow_arm64=True,
            custom_dependencies=(
                BrainboxImageBuilder.PytorchDependencies(
                    '2.7.0', 'cu128', True
                ),
                BrainboxImageBuilder.Dependencies(no_deps=True)
            ),
            repository=BrainboxImageBuilder.Repository(
                'https://github.com/FunAudioLLM/CosyVoice',
                '1dcc59676fe3fa863f983ab7820e481560c73be7',
                install=False,
                recursive_clone=True
            ),
            keep_dockerfile = True,
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            dont_rm=False
        )
    
    def post_install(self):
        if not self.resource_folder('pretrained_models').is_dir():
            self.run_with_configuration(self.get_service_run_configuration(None).as_service_worker('--install'))
        else:
            print('MODELS are already downloaded')

    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return CosyVoiceSettings()

    def create_api(self):
        from .api import CosyVoice
        return CosyVoice()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import CosyVoice

        api.execute(BrainBoxTask.call(CosyVoice).train(
            'lina',
            "One little spark, and before you know it, the whole world is burning.",
            File.read(Path(__file__).parent / 'lina.wav')
        ))


        yield (
            TestReport
            .last_call(api)
            .href('echo')
            .with_comment("Returns JSON with passed arguments and `success` fields")
        )

        result = api.execute(BrainBoxTask.call(CosyVoice).voice_to_text('lina', VOICEOVER_TEXT))
        tc.assertIsInstance(result, str)
        check_if_its_sound(api.open_file(result).content, tc)
        yield (
            TestReport
            .last_call(api)
            .href('voice_to_text')
            .result_is_file(File.Kind.Audio)
        )

        result = api.execute(BrainBoxTask.call(CosyVoice).voice_to_text_transligual('lina', "Ein einziger Funke, und unmerklich gerät die Welt in Brand."))
        tc.assertIsInstance(result, str)
        check_if_its_sound(api.open_file(result).content, tc)
        yield (
            TestReport
            .last_call(api)
            .href('voice_to_test_transligual')
            .result_is_file(File.Kind.Audio)
        )

        source = File.read(Path(__file__).parent / 'lina_ru.wav')
        result = api.execute(BrainBoxTask.call(CosyVoice).voice_to_file('lina', source))
        tc.assertIsInstance(result, str)
        check_if_its_sound(api.open_file(result).content, tc)
        yield (
            TestReport
            .last_call(api)
            .href('voice_file')
            .result_is_file(File.Kind.Audio)
        )
