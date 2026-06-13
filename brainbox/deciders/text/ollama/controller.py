from pathlib import Path
from typing import Iterable

from foundation_kaia.brainbox_utils import Installer
from ....framework import (
    BrainboxImageBuilder, IImageBuilder, RunConfiguration,
    DockerMarshallingController, SelfTestCase,
)
from .settings import OllamaSettings
from .image_builder import OllamaImageBuilder

OLLAMA_PORT = 11434
BRAINBOX_PORT = 8080


class OllamaController(DockerMarshallingController[OllamaSettings]):
    def get_image_builder(self) -> IImageBuilder:
        return OllamaImageBuilder(
            Path(__file__).parent,
            install_requirements_as_root=True,
            dependencies=(
                BrainboxImageBuilder.KaiaFoundationDependencies(),
            ),
        )

    def get_installer(self) -> Installer:
        from .app.model import OllamaInstaller
        return OllamaInstaller(self.resource_folder())

    def get_service_run_configuration(self, parameter: str | None) -> RunConfiguration:
        return RunConfiguration(
            parameter,
            publish_ports={self.connection_settings.port: BRAINBOX_PORT, OLLAMA_PORT: OLLAMA_PORT},
            mount_resource_folders={'main': '/home/ubuntu/.ollama'},
            command_line_arguments=[parameter] if parameter is not None else [],
        )

    def get_default_settings(self):
        return OllamaSettings()

    def create_api(self):
        from .api import OllamaApi
        return OllamaApi()

    def self_test_cases(self) -> Iterable[SelfTestCase]:
        from .api import Ollama
        model = self.settings.models_to_install[0]
        prompt = "The recipe for the borsch is as follows:"
        yield SelfTestCase(Ollama.new_task(parameter=model).completions_json(prompt=prompt), None)
        yield SelfTestCase(Ollama.new_task(parameter=model).completions(prompt=prompt), None)
        prompt = "Give me the recipe of the borsch."
        yield SelfTestCase(Ollama.new_task(parameter=model).question_json(prompt=prompt), None)
        yield SelfTestCase(Ollama.new_task(parameter=model).question(prompt=prompt), None)

        prompt = "Describe the supplied image"
        image = Path(__file__).parent/'image.png'
        #yield SelfTestCase(Ollama.new_task(parameter=model).question_json(prompt=prompt, image=image), None)
        #yield SelfTestCase(Ollama.new_task(parameter=model).question(prompt=prompt, image=image), None)

