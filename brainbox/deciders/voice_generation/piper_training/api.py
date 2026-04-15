from brainbox.framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from foundation_kaia.brainbox_utils.models import IModelInstallingSupport
from .controller import PiperTrainingController
from .settings import PiperTrainingSettings, PiperTrainingModels
from .app.installer import PiperTrainingModel
from .app.interface import PiperTrainingInterface, PiperTrainingParameters, CkptData



class PiperTrainingApi(
    DockerMarshallingApi[PiperTrainingSettings, PiperTrainingController],
    IModelInstallingSupport[PiperTrainingModel],
    PiperTrainingInterface
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class PiperTrainingTaskBuilder(
    TaskBuilder,
    IModelInstallingSupport[PiperTrainingModel],
    PiperTrainingInterface
):
    pass


class PiperTrainingEntryPoint(EntryPoint[PiperTrainingTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = PiperTrainingApi
        self.Controller = PiperTrainingController
        self.Settings = PiperTrainingSettings
        self.TrainingParameters = PiperTrainingParameters
        self.Models = PiperTrainingModels
        self.Checkpoint = CkptData

PiperTraining = PiperTrainingEntryPoint()
