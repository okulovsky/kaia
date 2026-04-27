from foundation_kaia.brainbox_utils import IInstallingSupport
from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import ZonosSettings
from .controller import ZonosController
from .app.interface import IZonos



class ZonosApi(
    DockerMarshallingApi[ZonosSettings, ZonosController],
    IZonos,
    IInstallingSupport,
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class ZonosTaskBuilder(
    TaskBuilder,
    IZonos,
    IInstallingSupport,
):
    pass


class ZonosEntryPoint(EntryPoint[ZonosTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = ZonosApi
        self.Settings = ZonosSettings
        self.Controller = ZonosController

    class Emotions:
        Happiness = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        Sadness   = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        Disgust   = [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        Fear      = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
        Surprise  = [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
        Anger     = [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
        Other     = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        Neutral   = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]

Zonos = ZonosEntryPoint()
