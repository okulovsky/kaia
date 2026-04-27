from foundation_kaia.brainbox_utils import IModelInstallingSupport, IModelLoadingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import CosyVoiceSettings
from .controller import CosyVoiceController
from .app.interface import ICosyVoice



class CosyVoiceApi(
    DockerMarshallingApi[CosyVoiceSettings, CosyVoiceController],
    ICosyVoice,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class CosyVoiceTaskBuilder(
    TaskBuilder,
    ICosyVoice,
    IModelLoadingSupport,
    IModelInstallingSupport[str],
):
    pass


class CosyVoiceEntryPoint(EntryPoint[CosyVoiceTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = CosyVoiceApi
        self.Settings = CosyVoiceSettings
        self.Controller = CosyVoiceController

CosyVoice = CosyVoiceEntryPoint()
