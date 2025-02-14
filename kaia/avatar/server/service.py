from typing import *
from  dataclasses import dataclass, field
from ..image_service import ImageService, ImageServiceSettings
from ..dubbing_service import DubbingService, TextLike, IDubCommandGenerator, DubbingServiceOutput, ParaphraseServiceSettings
from ..state import InitialStateFactory, State
import os
from pathlib import Path
from kaia.common import Loc
from brainbox import BrainBoxApi
from ..media_library_manager import MediaLibraryManager
from ..world import World
from ..recognition_service import RecognitionService, RecognitionSettings
from kaia.dub import IntentsPack, Template
from .interface import IAvatarApi
from brainbox.framework.common.marshalling import endpoint
from brainbox import File
from ..narration_service import NarrationService, NarrationSettings, NarrationReply


@dataclass
class AvatarSettings:
    initial_state_factory: InitialStateFactory = field(default_factory=lambda: InitialStateFactory.Simple({
        World.character.field_name: 'character_0'
    }))
    port: int = 8092
    brain_box_api: None | BrainBoxApi = None
    dubbing_task_generator: None|IDubCommandGenerator = None
    paraphrase_settings: None|ParaphraseServiceSettings = None
    image_settings: None|ImageServiceSettings = None
    narration_settings: None|NarrationSettings = None
    errors_folder: None|Path = Loc.data_folder/'avatar_errors'
    resemblyzer_model_name: str|None = None
    whisper_model: str = 'base'


class AvatarService(IAvatarApi):
    def __init__(self, settings: AvatarSettings):
        self.settings = settings
        self.state = self.settings.initial_state_factory.create('')
        self.dubbing_service = None
        if self.settings.dubbing_task_generator is not None and self.settings.brain_box_api is not None:
            self.dubbing_service = DubbingService(
                self.settings.dubbing_task_generator,
                self.settings.brain_box_api,
                self.settings.paraphrase_settings
            )

        self.image_service = None
        if self.settings.image_settings is not None:
            self.image_service = ImageService(
                self.settings.image_settings
            )

        self.recognition_service = RecognitionService(
            self.settings.brain_box_api,
            self.settings.resemblyzer_model_name,
            self.settings.whisper_model
        )

        self.narration_service = None
        if self.settings.narration_settings is not None:
            self.narration_service = NarrationService(self.settings.narration_settings, self.image_service)

    @endpoint(url='/dub/start', method='POST')
    def dub(self, text: TextLike) -> DubbingServiceOutput:
        if self.dubbing_service is None:
            raise ValueError("Dubbing service is not set")
        return self.dubbing_service.dub(self.state, text)

    @endpoint(url='/dub/result', method='GET')
    def dub_get_result(self, job_id: str) -> File:
        if self.dubbing_service is None:
            raise ValueError("Dubbing service is not set")
        return self.dubbing_service.get_result(job_id)

    @endpoint(url='/image/new', method='GET')
    def image_get_new(self, empty_image_if_none = True) -> Optional[File]:
        if self.image_service is None:
            raise ValueError("Image service not set")
        image = self.image_service.get_new_image(self.state)
        if image is None and empty_image_if_none:
            return _empty_image
        return image

    @endpoint(url='/image/current', method='GET')
    def image_get_current(self, empty_image_if_none=True) -> Optional[File]:
        if self.image_service is None:
            raise ValueError("Image service not set")
        image = self.image_service.get_current_image(self.state)
        if image is None and empty_image_if_none:
            return _empty_image
        return image

    @endpoint(url='/image/current_description', method='GET')
    def image_get_current_description(self) -> str|None:
        if self.image_service is None:
            return None
        return self.image_service.get_current_image_description(self.state)

    @endpoint(url='/image/empty', method='GET')
    def image_get_empty(self) -> File:
        return _empty_image

    @endpoint(url='/state/change', method="POST")
    def state_change(self, change: dict[str,Any]) -> NarrationReply:
        if self.narration_service is None:
            self.state.apply_change(change)
            return NarrationReply()
        else:
            return self.narration_service.apply_state_change(self.state, change)

    @endpoint(url='/state/get', method='GET')
    def state_get(self):
        return self.state.get_state()

    @endpoint(url='/image/report', method='POST')
    def image_report(self, report: str):
        if self.image_service is None:
            raise ValueError("Image service not set")
        return self.image_service.feedback(self.state, report)

    @endpoint(url='/recognition/train', method='POST')
    def recognition_train(self,
                         intents: tuple[IntentsPack,...],
                         replies: tuple[Template,...]
                         ):
        state = self.state
        state.initialize_intents_and_replies(intents, replies)
        self.recognition_service.train(state)

    @endpoint(url='/recognition/transcribe', method='POST')
    def recognition_transcribe(self, file_id: str, settings: RecognitionSettings):
        return self.recognition_service.transcribe(
            self.state,
            file_id,
            settings
        )

    @endpoint(url='/recognition/speaker/fix', method='POST')
    def recognition_speaker_fix(self, actual_speaker: str):
        return self.recognition_service.correct_speaker_recognition(
            self.state,
            actual_speaker
        )

    @endpoint(url='/recognition/speaker/train', method='POST')
    def recognition_speaker_train(self, media_library_path: Path):
        return self.recognition_service.speaker_train(media_library_path)

    @endpoint(url='/narration/randomize/character', method='POST')
    def narration_randomize_character(self) -> NarrationReply:
        if self.narration_service is None:
            return NarrationReply()
        return self.narration_service.randomize_character(self.state)

    @endpoint(url='/narration/randomize/activity', method='POST')
    def narration_randomize_activity(self) -> NarrationReply:
        if self.narration_service is None:
            return NarrationReply()
        return self.narration_service.randomize_activity(self.state)

    @endpoint(url='/narration/reset', method='POST')
    def narration_reset(self) -> NarrationReply:
        if self.narration_service is None:
            return NarrationReply()
        return self.narration_service.reset(self.state)

    @endpoint(url='/narration/tick', method='POST')
    def narration_tick(self) -> NarrationReply:
        if self.narration_service is None:
            return NarrationReply()
        return self.narration_service.tick(self.state)







_empty_image = File('empty.png',
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82',
                    File.Kind.Image
                    )