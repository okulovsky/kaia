from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .app.interface import ILlamaLoraServer
from .settings import LlamaLoraServerSettings
from .controller import LlamaLoraServerController


class LlamaLoraServerApi(DockerMarshallingApi[LlamaLoraServerSettings, LlamaLoraServerController], ILlamaLoraServer):
    def __init__(self, base_url: str):
        super().__init__(base_url)


class LlamaLoraServerTaskBuilder(TaskBuilder, ILlamaLoraServer):
    pass


class LlamaLoraServerEntryPoint(EntryPoint[LlamaLoraServerTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = LlamaLoraServerApi
        self.Settings = LlamaLoraServerSettings
        self.Controller = LlamaLoraServerController

LlamaLoraServer = LlamaLoraServerEntryPoint()
