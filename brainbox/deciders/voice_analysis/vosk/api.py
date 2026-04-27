from foundation_kaia.brainbox_utils import IModelInstallingSupport, IModelLoadingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import VoskSettings, VoskModels
from .controller import VoskController
from .app.interface import IVosk
from .app.model import VoskModelSpec



class VoskApi(
    DockerMarshallingApi[VoskSettings, VoskController],
    IVosk,
    IModelLoadingSupport,
    IModelInstallingSupport[VoskModelSpec],
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class VoskTaskBuilder(
    TaskBuilder,
    IVosk,
    IModelLoadingSupport,
    IModelInstallingSupport[VoskModelSpec],
):
    pass


class VoskEntryPoint(EntryPoint[VoskTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = VoskApi
        self.Models = VoskModels
        self.Settings = VoskSettings
        self.Controller = VoskController

Vosk = VoskEntryPoint()
