from brainbox.framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .controller import LlamaLoraSFTTrainerController
from .settings import LlamaLoraSFTTrainerSettings
from .app.interface import LlamaLoraSFTTrainerInterface, TrainingRun, TrainingSettings


class LlamaLoraSFTTrainerApi(
    DockerMarshallingApi[LlamaLoraSFTTrainerSettings, LlamaLoraSFTTrainerController],
    LlamaLoraSFTTrainerInterface,
):
    def __init__(self, base_url: str):
        super().__init__(base_url)


class LlamaLoraSFTTrainerTaskBuilder(
    TaskBuilder,
    LlamaLoraSFTTrainerInterface,
):
    pass


class LlamaLoraSFTTrainerEntryPoint(EntryPoint[LlamaLoraSFTTrainerTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = LlamaLoraSFTTrainerApi
        self.Controller = LlamaLoraSFTTrainerController
        self.Settings = LlamaLoraSFTTrainerSettings
        self.TrainingSettings = TrainingSettings
        self.TrainingRun = TrainingRun

LlamaLoraSFTTrainer = LlamaLoraSFTTrainerEntryPoint()
