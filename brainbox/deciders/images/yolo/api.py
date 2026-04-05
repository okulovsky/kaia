from foundation_kaia.brainbox_utils import IModelInstallingSupport, IModelLoadingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import YoloSettings, YoloModels
from .controller import YoloController
from .app.interface import IYolo



class YoloApi(
    DockerMarshallingApi[YoloSettings, YoloController],
    IYolo,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class YoloTaskBuilder(
    TaskBuilder,
    IYolo,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    pass


class YoloEntryPoint(EntryPoint[YoloTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = YoloApi
        self.Models = YoloModels
        self.Settings = YoloSettings
        self.Controller = YoloController

Yolo = YoloEntryPoint()
