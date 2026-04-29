from foundation_kaia.brainbox_utils import IInstallingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import ChromaSettings
from .controller import ChromaController
from .app.interface import IChroma


class ChromaApi(
    DockerMarshallingApi[ChromaSettings, ChromaController],
    IChroma,
    IInstallingSupport,
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class ChromaTaskBuilder(
    TaskBuilder,
    IChroma,
    IInstallingSupport,
):
    pass


class ChromaEntryPoint(EntryPoint[ChromaTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = ChromaApi
        self.Settings = ChromaSettings
        self.Controller = ChromaController


Chroma = ChromaEntryPoint()
