from foundation_kaia.brainbox_utils.models import IModelInstallingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import ComfyUISettings
from .controller import ComfyUIController
from .app.interface import IComfyUI
from .app.model import ComfyUIInstallation


class ComfyUIApi(
    DockerMarshallingApi[ComfyUISettings, ComfyUIController],
    IComfyUI,
    IModelInstallingSupport[ComfyUIInstallation],
):
    def __init__(self, base_url: str):
        super().__init__(base_url)


class ComfyUITaskBuilder(
    TaskBuilder,
    IComfyUI,
    IModelInstallingSupport[ComfyUIInstallation],
):
    pass


class ComfyUIEntryPoint(EntryPoint[ComfyUITaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = ComfyUIApi
        self.Settings = ComfyUISettings
        self.Controller = ComfyUIController


ComfyUI = ComfyUIEntryPoint()
