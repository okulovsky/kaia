from ....framework import DockerMarshallingApi,EntryPoint, TaskBuilder
from foundation_kaia.brainbox_utils.models import IInstallingSupport
from .controller import VideoToImagesController
from .settings import VideoToImagesSettings
from .app.interface import VideoToImagesInterface, AnalysisSettings



class VideoToImagesApi(
    DockerMarshallingApi[VideoToImagesSettings, VideoToImagesController],
    IInstallingSupport,
    VideoToImagesInterface,
):
    def __init__(self, base_url: str):
        super().__init__(base_url)


class VideoToImagesTaskBuilder(
    TaskBuilder,
    IInstallingSupport,
    VideoToImagesInterface,
):
    pass


class VideoToImagesEntryPoint(EntryPoint[VideoToImagesTaskBuilder]):
    def __init__(self):
        super().__init__()
        self.Api = VideoToImagesApi
        self.Controller = VideoToImagesController
        self.Settings = VideoToImagesSettings
        self.AnalysisSettings = AnalysisSettings

VideoToImages = VideoToImagesEntryPoint()
