from brainbox.framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .controller import OneTrainerController
from .settings import OneTrainerSettings
from .app.interface import OneTrainerInterface, OneTrainerParameters, CheckpointInfo


class OneTrainerApi(
    DockerMarshallingApi[OneTrainerSettings, OneTrainerController],
    OneTrainerInterface,
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class OneTrainerTaskBuilder(TaskBuilder, OneTrainerInterface):
    pass


class OneTrainerEntryPoint(EntryPoint[OneTrainerTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = OneTrainerApi
        self.Controller = OneTrainerController
        self.Settings = OneTrainerSettings
        self.Parameters = OneTrainerParameters
        self.Checkpoint = CheckpointInfo


OneTrainer = OneTrainerEntryPoint()
