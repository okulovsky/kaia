from foundation_kaia.brainbox_utils import IModelInstallingSupport, IModelLoadingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import WhisperSettings, WhisperModels
from .controller import WhisperController
from .app.interface import IWhisper



class WhisperApi(
    DockerMarshallingApi[WhisperSettings, WhisperController],
    IWhisper,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class WhisperTaskBuilder(
    TaskBuilder,
    IWhisper,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    pass


class WhisperEntryPoint(EntryPoint[WhisperTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = WhisperApi
        self.Models = WhisperModels
        self.Settings = WhisperSettings
        self.Controller = WhisperController

    def get_ordering_arguments_sequence(self) -> tuple[str, ...] | None:
        return ('model',)

Whisper = WhisperEntryPoint()
