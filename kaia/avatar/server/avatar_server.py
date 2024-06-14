from typing import *
import dataclasses
import pathlib
from kaia.infra.marshalling_api import MarshallingEndpoint
import flask
from .image_service import IImageService
from .dubbing_service import IDubbingService
from ..narrator import INarrator

class AvatarEndpoints:
    dub_utterance = MarshallingEndpoint('/dub/utterance')
    dub_string = MarshallingEndpoint('/dub/string')
    image_get = MarshallingEndpoint('/image/get')
    image_report = MarshallingEndpoint('/image/report')
    state_change = MarshallingEndpoint('/state/change')
    state_get = MarshallingEndpoint('/state/get')


@dataclasses.dataclass
class AvatarSettings:
    port: int = 8092


class AvatarWebServer:
    def __init__(self,
                 settings: AvatarSettings,
                 narrator: INarrator,
                 dubbing_service: IDubbingService,
                 image_service: IImageService,
                 errors_folder: pathlib.Path,
                 ):
        self.settings = settings
        self.narrator = narrator
        self.dubbing_service = dubbing_service
        self.image_service = image_service
        self.errors_folder = errors_folder

    def __call__(self):
        self.app = flask.Flask('avatar')
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        binder = MarshallingEndpoint.Binder(self.app, self.errors_folder)
        binder.bind_all(AvatarEndpoints, self)
        self.app.run('0.0.0.0',self.settings.port)

    def index(self):
        return 'Avatar server is up'

    def dub_utterance(self, utterances):
        return self.dubbing_service.dub_utterance(utterances, self.narrator.get_voice())


    def dub_string(self, string):
        return self.dubbing_service.dub_string(string, self.narrator.get_voice())

    def image_get(self):
        return self.image_service.get_image(self.narrator.get_image_tags())

    def state_change(self, change: dict[str,Any]):
        self.narrator.apply_change(change)

    def state_get(self):
        return self.narrator.get_state()

    def image_report(self, report: str):
        return self.image_service.feedback(report)





