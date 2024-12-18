from .settings import OllamaSettings
from ..arch import DockerService, BrainBoxServiceRunner, LocalImageInstaller
from unittest import TestCase
from ...core import BrainBoxApi, BrainBoxTask, File, IntegrationTestResult, IApiDecider
from .api import Ollama
from pathlib import Path
import json


class OllamaInstaller(LocalImageInstaller):
    def __init__(self, settings: OllamaSettings):
        self.settings = settings

        service = DockerService(
            self,
            settings.port,
            settings.startup_time_in_seconds,
            BrainBoxServiceRunner(
                publish_ports={self.settings.port: 11434},
                mount_resource_folders={'main': "/root/.ollama"},
                gpu_required=BrainBoxServiceRunner.GpuRequirement.Mandatory,
                mount_data_folder=False,
                run_as_root=True,
            )
        )
        super().__init__(
            'ollama',
            Path(__file__).parent/'container',
            DOCKERFILE,
            None,
            service
        )


    def create_api(self) -> Ollama:
        return Ollama(f'{self.ip_address}:{self.settings.port}')

    def create_pull_service(self, model_name):
        return self.main_service.as_service_worker('pull', model_name)


    def post_install(self):
        for model in self.settings.models_to_install:
            path_to_model_manifest = self.resource_folder('main')/'models/manifests/registry.ollama.ai/library'/model.location
            if not path_to_model_manifest.is_file():
                self.create_pull_service(model.name).run()

    def create_brainbox_decider_api(self, parameters: str) -> IApiDecider:
        return Ollama(f'{self.ip_address}:{self.settings.port}').with_model(parameters)

    def warmup(self, parameters: str):
        self.main_service._container_runner.command_line_arguments=['run', parameters]
        self.run_if_not_running_and_wait()


    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase):
        for model in self.settings.models_to_install:
            yield IntegrationTestResult(0, "Model "+model.name)

            yield IntegrationTestResult(1, 'Completions')

            prompt = "The recipe for the borsch is as follows:"
            yield IntegrationTestResult(2, "Prompt", prompt)

            result = api.execute(BrainBoxTask.call(Ollama).completions_json(prompt=prompt).to_task(model.name))
            yield IntegrationTestResult(2, "Json", File("", json.dumps(result), File.Kind.Json))

            result = api.execute(BrainBoxTask.call(Ollama).completions(prompt=prompt).to_task(model.name))
            tc.assertIsInstance(result, str)
            yield IntegrationTestResult(2, "Text", result)

            yield IntegrationTestResult(1, 'Chat completions')

            prompt = "Give me the recipe of the borsch."
            yield IntegrationTestResult(2, "Prompt", prompt)

            result = api.execute(BrainBoxTask.call(Ollama).question_json(prompt=prompt).to_task(model.name))
            yield IntegrationTestResult(2, "Json", File("", json.dumps(result), File.Kind.Json))

            result = api.execute(BrainBoxTask.call(Ollama).question(prompt=prompt).to_task(model.name))
            tc.assertIsInstance(result, str)
            yield IntegrationTestResult(2, "Text", result)




DOCKERFILE = '''
FROM ollama/ollama

COPY run.sh /bin/run.sh

ENTRYPOINT ["/bin/bash", "/bin/run.sh"]
'''




