from foundation_kaia.brainbox_utils import IInstallingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import WhisperKenLMSettings
from .controller import WhisperKenLMController
from .app.interface import IWhisperKenLM


class WhisperKenLMApi(
    DockerMarshallingApi[WhisperKenLMSettings, WhisperKenLMController],
    IWhisperKenLM,
    IInstallingSupport,
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class WhisperKenLMTaskBuilder(
    TaskBuilder,
    IWhisperKenLM,
    IInstallingSupport,
):
    pass


class WhisperKenLMEntryPoint(EntryPoint[WhisperKenLMTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api        = WhisperKenLMApi
        self.Settings   = WhisperKenLMSettings
        self.Controller = WhisperKenLMController


WhisperKenLM = WhisperKenLMEntryPoint()
