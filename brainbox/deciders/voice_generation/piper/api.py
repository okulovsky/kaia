from foundation_kaia.brainbox_utils import IModelInstallingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import PiperSettings, PiperModels
from .controller import PiperController
from .app.interface import IPiper
from .app.model import PiperModelSpec



class PiperApi(
    DockerMarshallingApi[PiperSettings, PiperController],
    IPiper,
    IModelInstallingSupport[PiperModelSpec],
):
    def __init__(self, base_url: str):
        super().__init__(base_url)


class PiperTaskBuilder(
    TaskBuilder,
    IPiper,
    IModelInstallingSupport[PiperModelSpec],
):
    pass


class PiperEntryPoint(EntryPoint[PiperTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = PiperApi
        self.Models = PiperModels
        self.Settings = PiperSettings
        self.Controller = PiperController

Piper = PiperEntryPoint()
