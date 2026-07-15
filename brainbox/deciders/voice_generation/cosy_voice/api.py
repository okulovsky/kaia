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
    def __init__(self, base_url: str):
        super().__init__(base_url)


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
