from foundation_kaia.brainbox_utils import IModelInstallingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .app.interface import IOllama, OllamaOptions
from .settings import OllamaSettings
from .controller import OllamaController


class OllamaApi(
    DockerMarshallingApi[OllamaSettings, OllamaController],
    IOllama,
    IModelInstallingSupport[str],
):
    def __init__(self, base_url: str):
        super().__init__(base_url)


class OllamaTaskBuilder(
    TaskBuilder,
    IOllama,
    IModelInstallingSupport[str],
):
    pass


class OllamaEntryPoint(EntryPoint[OllamaTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = OllamaApi
        self.Controller = OllamaController
        self.Settings = OllamaSettings
        self.Options: type = OllamaOptions

Ollama = OllamaEntryPoint()
