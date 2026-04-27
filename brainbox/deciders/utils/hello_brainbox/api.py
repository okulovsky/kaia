from foundation_kaia.brainbox_utils import IModelInstallingSupport, IModelLoadingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import HelloBrainBoxSettings, HelloBrainBoxModels
from .controller import HelloBrainBoxController
from .app.interface import IHelloBrainBox
from .app.model import HelloBrainBoxModelSpec



class HelloBrainBoxApi(
    DockerMarshallingApi[HelloBrainBoxSettings, HelloBrainBoxController],
    IHelloBrainBox,
    IModelLoadingSupport,
    IModelInstallingSupport[HelloBrainBoxModelSpec],
):
    def __init__(self, address: str|None = None):
        super().__init__(address)

class HelloBrainBoxTaskBuilder(
    TaskBuilder,
    IHelloBrainBox,
    IModelLoadingSupport,
    IModelInstallingSupport[HelloBrainBoxModelSpec]
):
    pass


class HelloBrainBoxEntryPoint(EntryPoint[HelloBrainBoxTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = HelloBrainBoxApi
        self.Models = HelloBrainBoxModels
        self.Settings = HelloBrainBoxSettings
        self.Controller = HelloBrainBoxController

HelloBrainBox = HelloBrainBoxEntryPoint()