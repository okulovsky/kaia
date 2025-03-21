from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, IModelDownloadingController, DownloadableModel
)
from .settings import OllamaSettings, OllamaModel
from pathlib import Path
from yo_fluq import FileIO


class OllamaController(DockerWebServiceController[OllamaSettings], IModelDownloadingController):
    def get_downloadable_model_type(self) -> type[DownloadableModel]:
        return OllamaModel

    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            None
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is None:
            raise ValueError(f"`parameter` cannot be None for {self.get_name()}")
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port: 11434},
            mount_resource_folders={'main': "/root/.ollama"},
            mount_top_resource_folder=False,
            command_line_arguments=['run',parameter],
            run_as_root=True,
        )

    def get_default_settings(self):
        return OllamaSettings()

    def create_api(self):
        from .api import Ollama
        return Ollama()

    def pre_install(self):
        path = Path(__file__).parent/'container/run.sh'
        sh = FileIO.read_text(path)
        sh = sh.replace('\r','')
        FileIO.write_bytes(sh.encode('ascii'), path)

    def post_install(self):
        self.download_models(self.settings.models_to_install)

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import Ollama
        model = self.settings.models_to_install[0]
        prompt = "The recipe for the borsch is as follows:"
        api.execute(BrainBoxTask.call(Ollama, model.name).completions_json(prompt=prompt))
        yield TestReport.last_call(api).href('completions-json').with_comment("Returns json for completions with detailed reply")

        api.execute(BrainBoxTask.call(Ollama, model.name).completions(prompt=prompt))
        yield TestReport.last_call(api).href('completions-txt').with_comment("Returns only the text result")

        prompt = "Give me the recipe of the borsch."
        api.execute(BrainBoxTask.call(Ollama, model.name).question_json(prompt=prompt))
        yield TestReport.last_call(api).href('question-json').with_comment("Returns json for question mode with detailed reply")

        api.execute(BrainBoxTask.call(Ollama, model.name).question(prompt=prompt))
        yield TestReport.last_call(api).href('question-txt').with_comment("Returns only the text result")



DOCKERFILE = '''
FROM ollama/ollama

COPY run.sh /bin/run.sh

ENTRYPOINT ["/bin/bash", "/bin/run.sh"]
'''

