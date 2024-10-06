from typing import *
from  dataclasses import dataclass, field
import pathlib
from kaia.infra.marshalling_api import MarshallingEndpoint
import flask
from .image_service import ImageService
from .dubbing_service import DubbingService, TextLike, IDubTaskGenerator
from .state import InitialStateFactory, State
import os
from pathlib import Path
from kaia.infra import Loc
from kaia.brainbox import BrainBoxApi
from .media_library_manager import MediaLibraryManager
from copy import deepcopy
from kaia.narrator import World
from .recognition_service import RecognitionService, RecognitionSettings
from kaia.dub import IntentsPack, Template

class AvatarEndpoints:
    dub = MarshallingEndpoint('/dub/dub')
    dub_get_result = MarshallingEndpoint('/dub/get_result')
    image_get = MarshallingEndpoint('/image/get')
    image_report = MarshallingEndpoint('/image/report')
    state_change = MarshallingEndpoint('/state/change')
    state_get = MarshallingEndpoint('/state/get')
    recognition_transcribe = MarshallingEndpoint('/recognition/transcribe')
    recognition_train = MarshallingEndpoint('/recognition/train')
    recognition_speaker_fix = MarshallingEndpoint('/recognition/speaker_fix')
    recognition_speaker_train = MarshallingEndpoint('/recognition/speaker_train')






@dataclass
class AvatarSettings:
    initial_state_factory: InitialStateFactory = field(default_factory=lambda: InitialStateFactory.Simple({
        World.character.field_name: 'character_0'
    }))
    port: int = 8092
    brain_box_api: None | BrainBoxApi = None
    dubbing_task_generator: None|IDubTaskGenerator = None
    paraphrase_media_library_manager: None|MediaLibraryManager = None
    image_media_library_manager: None|MediaLibraryManager = None
    errors_folder: None|Path = Loc.data_folder/'avatar_errors'
    resemblyzer_model_name: str|None = None
    whisper_model: str = 'base'


class AvatarServer:
    def __init__(self, settings: AvatarSettings):
        self.settings = settings
        self.session_to_state: dict[str, State] = {}
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

        self.recognition_service = RecognitionService(
            self.settings.brain_box_api,
            self.settings.resemblyzer_model_name,
            self.settings.whisper_model
        )


    def _get_state(self, session_id: str) -> State:
        if session_id not in self.session_to_state:
            self.session_to_state[session_id] = self.settings.initial_state_factory.create(session_id)
            self.session_to_state[session_id]._session_id = session_id
        return self.session_to_state[session_id]


    def __call__(self):
        self.app = flask.Flask('avatar')
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        binder = MarshallingEndpoint.Binder(self.app, self.settings.errors_folder)
        binder.bind_all(AvatarEndpoints, self)
        self.app.run('0.0.0.0',self.settings.port)

    def index(self):
        return 'Avatar server is up'

    def dub(self, session_id: str, text: TextLike):
        if self.dubbing_service is None:
            raise ValueError("Dubbing service is not set")
        return self.dubbing_service.dub(self._get_state(session_id), text)

    def dub_get_result(self, job_id: str):
        if self.dubbing_service is None:
            raise ValueError("Dubbing service is not set")
        return self.dubbing_service.get_result(job_id)

    def image_get(self, session_id: str):
        if self.image_service is None:
            raise ValueError("Image service not set")
        return self.image_service.get_image(self._get_state(session_id))

    def state_change(self, session_id: str, change: dict[str,Any]):
        self._get_state(session_id).apply_change(change)

    def state_get(self, session_id: str):
        return self._get_state(session_id).get_state()


    def image_report(self, session_id: str, report: str):
        if self.image_service is None:
            raise ValueError("Image service not set")
        return self.image_service.feedback(self._get_state(session_id), report)

    def recognition_train(self,
                         session_id: str,
                         intents: tuple[IntentsPack,...],
                         replies: tuple[Template,...]
                         ):
        state = self._get_state(session_id)
        state.initialize_intents_and_replies(intents, replies)
        self.recognition_service.train(state)

    def recognition_transcribe(self, session_id: str, file_id: str, settings: RecognitionSettings):
        return self.recognition_service.transcribe(
            self._get_state(session_id),
            file_id,
            settings
        )

    def recognition_speaker_fix(self, session_id: str, actual_speaker: str):
        return self.recognition_service.correct_speaker_recognition(
            self._get_state(session_id),
            actual_speaker
        )

    def recognition_speaker_train(self, session_id: str, media_library_path: Path):
        return self.recognition_service.speaker_train(
            self._get_state(session_id),
            media_library_path
        )

    def terminate(self):
        os._exit(1)


