from foundation_kaia.brainbox_utils import IInstallingSupport

from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .app.interface import IWakewordTraining
from .controller import WakewordTrainingController
from .settings import WakewordTrainingSettings


class WakewordTrainingApi(
    DockerMarshallingApi[WakewordTrainingSettings, WakewordTrainingController],
    IWakewordTraining,
    IInstallingSupport,
):
    pass


class WakewordTrainingTaskBuilder(TaskBuilder, IWakewordTraining, IInstallingSupport):
    pass


class WakewordTrainingEntryPoint(EntryPoint[WakewordTrainingTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = WakewordTrainingApi
        self.Controller = WakewordTrainingController
        self.Settings = WakewordTrainingSettings


WakewordTraining = WakewordTrainingEntryPoint()
