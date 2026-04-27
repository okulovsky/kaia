from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import ResemblyzerSettings
from .controller import ResemblyzerController
from .app.interface import IResemblyzer



class ResemblyzerApi(
    DockerMarshallingApi[ResemblyzerSettings, ResemblyzerController],
    IResemblyzer,
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class ResemblyzerTaskBuilder(
    TaskBuilder,
    IResemblyzer,
):
    pass


class ResemblyzerEntryPoint(EntryPoint[ResemblyzerTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = ResemblyzerApi
        self.Controller = ResemblyzerController
        self.Settings = ResemblyzerSettings

Resemblyzer = ResemblyzerEntryPoint()
