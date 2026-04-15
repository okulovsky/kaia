from foundation_kaia.brainbox_utils import IModelInstallingSupport, IModelLoadingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import InsightFaceSettings, InsightFaceModels
from .controller import InsightFaceController
from .app.interface import IInsightFace
from .app.model import InsightFaceModelSpec



class InsightFaceApi(
    DockerMarshallingApi[InsightFaceSettings, InsightFaceController],
    IInsightFace,
    IModelLoadingSupport,
    IModelInstallingSupport[InsightFaceModelSpec],
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class InsightFaceTaskBuilder(
    TaskBuilder,
    IInsightFace,
    IModelLoadingSupport,
    IModelInstallingSupport[InsightFaceModelSpec],
):
    pass


class InsightFaceEntryPoint(EntryPoint[InsightFaceTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = InsightFaceApi
        self.Models = InsightFaceModels
        self.Settings = InsightFaceSettings
        self.Controller = InsightFaceController

InsightFace = InsightFaceEntryPoint()
