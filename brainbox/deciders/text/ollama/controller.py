from typing import Iterable
from ....framework import (
    RunConfiguration, SelfTestCase, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
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
        from .api import OllamaApi
        return OllamaApi()

    def pre_install(self):
        path = Path(__file__).parent/'container/run.sh'
        sh = FileIO.read_text(path)
        sh = sh.replace('\r','')
        FileIO.write_bytes(sh.encode('ascii'), path)

    def post_install(self):
        self.download_models(self.settings.models_to_install)

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Ollama
        model = self.settings.models_to_install[0]
        prompt = "The recipe for the borsch is as follows:"
        yield SelfTestCase(Ollama.new_task(parameter=model.name).completions_json(prompt=prompt), None)
        yield SelfTestCase(Ollama.new_task(parameter=model.name).completions(prompt=prompt), None)
        prompt = "Give me the recipe of the borsch."
        yield SelfTestCase(Ollama.new_task(parameter=model.name).question_json(prompt=prompt), None)
        yield SelfTestCase(Ollama.new_task(parameter=model.name).question(prompt=prompt), None)



DOCKERFILE = '''
FROM ollama/ollama

COPY run.sh /bin/run.sh

ENTRYPOINT ["/bin/bash", "/bin/run.sh"]
'''

