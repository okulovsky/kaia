from foundation_kaia.brainbox_utils import IInstallingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import ChatterboxSettings
from .controller import ChatterboxController
from .app.interface import IChatterbox



class ChatterboxApi(
    DockerMarshallingApi[ChatterboxSettings, ChatterboxController],
    IChatterbox,
    IInstallingSupport,
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class ChatterboxTaskBuilder(
    TaskBuilder,
    IChatterbox,
    IInstallingSupport,
):
    pass


class ChatterboxEntryPoint(EntryPoint[ChatterboxTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = ChatterboxApi
        self.Settings = ChatterboxSettings
        self.Controller = ChatterboxController

Chatterbox = ChatterboxEntryPoint()
