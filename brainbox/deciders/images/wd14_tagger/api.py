from foundation_kaia.brainbox_utils import IModelInstallingSupport, IModelLoadingSupport
from ....framework import DockerMarshallingApi,EntryPoint, TaskBuilder
from .settings import WD14TaggerSettings, WD14TaggerModels
from .controller import WD14TaggerController
from .app.interface import IWD14Tagger



class WD14TaggerApi(
    DockerMarshallingApi[WD14TaggerSettings, WD14TaggerController],
    IWD14Tagger,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class WD14TaggerTaskBuilder(
    TaskBuilder,
    IWD14Tagger,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    pass


class WD14TaggerEntryPoint(EntryPoint[WD14TaggerTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = WD14TaggerApi
        self.Models = WD14TaggerModels
        self.Settings = WD14TaggerSettings
        self.Controller = WD14TaggerController

WD14Tagger = WD14TaggerEntryPoint()
