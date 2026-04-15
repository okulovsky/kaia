from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .controller import WhisperXController
from .settings import WhisperXSettings
from .app.interface import WhisperXInterface



class WhisperXApi(
    DockerMarshallingApi[WhisperXSettings, WhisperXController],
    WhisperXInterface,
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class WhisperXTaskBuilder(
    TaskBuilder,
    WhisperXInterface,
):
    pass


class WhisperXEntryPoint(EntryPoint[WhisperXTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = WhisperXApi
        self.Controller = WhisperXController
        self.Settings = WhisperXSettings

WhisperX = WhisperXEntryPoint()
