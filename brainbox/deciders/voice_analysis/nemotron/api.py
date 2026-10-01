from foundation_kaia.brainbox_utils import IModelInstallingSupport, IModelLoadingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import NemotronSettings, NemotronModels
from .controller import NemotronController
from .app.interface import INemotron
from .app.model import NemotronModelSpec


class NemotronApi(
    DockerMarshallingApi[NemotronSettings, NemotronController],
    INemotron,
    IModelLoadingSupport,
    IModelInstallingSupport[NemotronModelSpec],
):
    def __init__(self, base_url: str):
        super().__init__(base_url)


class NemotronTaskBuilder(
    TaskBuilder,
    INemotron,
    IModelLoadingSupport,
    IModelInstallingSupport[NemotronModelSpec],
):
    pass


class NemotronEntryPoint(EntryPoint[NemotronTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = NemotronApi
        self.Models = NemotronModels
        self.Settings = NemotronSettings
        self.Controller = NemotronController

Nemotron = NemotronEntryPoint()
