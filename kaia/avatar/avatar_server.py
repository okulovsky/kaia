from typing import *
from  dataclasses import dataclass, field
import pathlib
from kaia.infra.marshalling_api import MarshallingEndpoint
import flask
from .image_service import ImageService
from .dubbing_service import DubbingService, TextLike, IDubTaskGenerator
from ..narrator import INarrator, SimpleNarrator
import os
from pathlib import Path
from kaia.infra import Loc
from kaia.brainbox import BrainBoxApi
from .media_library_manager import MediaLibraryManager
from copy import deepcopy

class AvatarEndpoints:
    dub = MarshallingEndpoint('/dub/dub')
    dub_get_result = MarshallingEndpoint('/dub/get_result')
    image_get = MarshallingEndpoint('/image/get')
    image_report = MarshallingEndpoint('/image/report')
    state_change = MarshallingEndpoint('/state/change')
    state_get = MarshallingEndpoint('/state/get')


@dataclass
class AvatarSettings:
    port: int = 8092
    brain_box_api: None | BrainBoxApi = None
    narrator: INarrator = field(default_factory=lambda: SimpleNarrator('character_0'))
    dubbing_task_generator: None|IDubTaskGenerator = None
    paraphrase_media_library_manager: None|MediaLibraryManager = None
    image_media_library_manager: None|MediaLibraryManager = None
    errors_folder: None|Path = Loc.data_folder/'avatar_errors'


class AvatarWebServer:
    def __init__(self, settings: AvatarSettings):
        self.settings = settings
        self.narrator = deepcopy(self.settings.narrator)

        self.dubbing_service = None
        if self.settings.dubbing_task_generator is not None and self.settings.brain_box_api is not None:
            self.dubbing_service = DubbingService(
                self.settings.dubbing_task_generator,
                self.settings.brain_box_api,
                self.settings.paraphrase_media_library_manager
            )

        self.image_service = None
        if self.settings.image_media_library_manager is not None:
            self.image_service = ImageService(
                self.settings.image_media_library_manager
            )


    def __call__(self):
        self.app = flask.Flask('avatar')
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        binder = MarshallingEndpoint.Binder(self.app, self.settings.errors_folder)
        binder.bind_all(AvatarEndpoints, self)
        self.app.run('0.0.0.0',self.settings.port)

    def index(self):
        return 'Avatar server is up'

    def dub(self, text: TextLike):
        if self.dubbing_service is None:
            raise ValueError("Dubbing service is not set")
        return self.dubbing_service.dub(text, self.narrator.get_state())

    def dub_get_result(self, job_id: str):
        if self.dubbing_service is None:
            raise ValueError("Dubbing service is not set")
        return self.dubbing_service.get_result(job_id)

    def image_get(self):
        if self.image_service is None:
            raise ValueError("Image service not set")
        return self.image_service.get_image(self.narrator.get_state())

    def state_change(self, change: dict[str,Any]):
        self.narrator.apply_change(change)

    def state_get(self):
        return self.narrator.get_state()

    def image_report(self, report: str):
        if self.image_service is None:
            raise ValueError("Image service not set")
        return self.image_service.feedback(report)


    def terminate(self):
        os._exit(1)


