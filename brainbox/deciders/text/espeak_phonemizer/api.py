from ....framework import DockerMarshallingApi, EntryPoint, TaskBuilder
from .settings import EspeakPhonemizerSettings
from .controller import EspeakPhonemizerController
from .app.interface import IEspeakPhonemizer



class EspeakPhonemizerApi(
    DockerMarshallingApi[EspeakPhonemizerSettings, EspeakPhonemizerController],
    IEspeakPhonemizer,
):
    def __init__(self, address: str | None = None):
        super().__init__(address)


class EspeakPhonemizerTaskBuilder(
    TaskBuilder,
    IEspeakPhonemizer,
):
    pass


class EspeakPhonemizerEntryPoint(EntryPoint[EspeakPhonemizerTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = EspeakPhonemizerApi
        self.Settings = EspeakPhonemizerSettings
        self.Controller = EspeakPhonemizerController

EspeakPhonemizer = EspeakPhonemizerEntryPoint()
