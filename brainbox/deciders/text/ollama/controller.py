from typing import Iterable
from unittest import TestCase
from ....framework import (
    RunConfiguration, TestReport, SmallImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, FileIO, INotebookableController, LocalExecutor
)
from .settings import OllamaSettings
from pathlib import Path


class OllamaController(DockerWebServiceController[OllamaSettings]):
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

    def post_install(self):
        for model in self.settings.models_to_install:
            path_to_model_manifest = (
                    self.resource_folder('main') /
                    'models/manifests/registry.ollama.ai/library' /
                    model.location
            )
            if not path_to_model_manifest.is_file():
                self.run_auxiliary_configuration(self.get_service_run_configuration('').as_service_worker('pull', model.name))

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable[TestReport.Item]:
        from .api import Ollama
        for model in self.settings.models_to_install:
            yield TestReport.H1("Model " + model.name)

            yield TestReport.H1('Completions')

            prompt = "The recipe for the borsch is as follows:"
            yield TestReport.text("Prompt")
            yield TestReport.text(prompt)

            result = api.execute(BrainBoxTask.call(Ollama, model.name).completions_json(prompt=prompt))
            yield TestReport.text("Json result:")
            yield TestReport.json(result)

            result = api.execute(BrainBoxTask.call(Ollama, model.name).completions(prompt=prompt))
            yield TestReport.text("Text result:")
            tc.assertIsInstance(result, str)
            yield TestReport.text(result)

            yield TestReport.H2('Questions')

            prompt = "Give me the recipe of the borsch."
            yield TestReport.text("Prompt")
            yield TestReport.text(prompt)

            result = api.execute(BrainBoxTask.call(Ollama, model.name).question_json(prompt=prompt))
            yield TestReport.text("Json result:")
            yield TestReport.json(result)

            result = api.execute(BrainBoxTask.call(Ollama, model.name).question(prompt=prompt))
            yield TestReport.text("Text result:")
            tc.assertIsInstance(result, str)
            yield TestReport.text(result)



DOCKERFILE = '''
FROM ollama/ollama

COPY run.sh /bin/run.sh

ENTRYPOINT ["/bin/bash", "/bin/run.sh"]
'''

