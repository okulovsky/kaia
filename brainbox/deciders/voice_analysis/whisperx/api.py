from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .controller import WhisperXController
from .settings import WhisperXSettings
from .app.interface import WhisperXInterface



class WhisperXApi(
    DockerMarshallingApi[WhisperXSettings, WhisperXController],
    WhisperXInterface,
):
    def __init__(self, base_url: str):
        super().__init__(base_url)


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
