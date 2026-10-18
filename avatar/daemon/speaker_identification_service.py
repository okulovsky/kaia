import traceback
from typing import Any
from brainbox.deciders import Resemblyzer
from .common import SoundEvent, IMessage, message_handler, State, AvatarService, InitializationEvent
from .common.vector_identificator import VectorIdentificator, IStrategy
from .brainbox_service import BrainBoxService
from dataclasses import dataclass
from foundation_kaia.marshalling import FileLike
from ..app import AvatarApi


@dataclass
class SpeakerIdentificationTrain(IMessage):
    file_id: str
    actual_user: str

@dataclass
class SpeakerIdentificationEvent(IMessage):
    file_id: str
    speaker: str|None
    error: Any = None



class SpeakerIdentificationService(AvatarService):
    Train = SpeakerIdentificationTrain
    Event = SpeakerIdentificationEvent

    def __init__(self,
                 avatar_api: AvatarApi,
                 identification_strategy: IStrategy,
                 ):
        self.avatar_api = avatar_api
        self.identification_strategy = identification_strategy

        self.buffer: list[tuple[SoundEvent,str]] = []
        self.vector_identificator: VectorIdentificator|None = None

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def on_initialize(self, message: InitializationEvent) -> None:
        self.vector_identificator = VectorIdentificator(
            self.avatar_api,
            self.resources_folder/'current',
            self.identification_strategy,
            self.sample_to_vector,
        )
        self.vector_identificator.initialize()


    def sample_to_vector(self, file: FileLike):
        command = BrainBoxService.Command(Resemblyzer.new_task().vector(file))
        return self.client.run_synchronously(command, BrainBoxService.Confirmation).result

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def on_sound_event(self, message: SoundEvent) -> SpeakerIdentificationEvent:
        try:
            speaker = self.vector_identificator.analyze(message.file_id)
        except Exception:
            return SpeakerIdentificationEvent(message.file_id, None, traceback.format_exc())
        return SpeakerIdentificationEvent(message.file_id, speaker)


    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def train(self, message: SpeakerIdentificationTrain) -> None:
        self.vector_identificator.add_sample(message.actual_user, message.file_id)
        self.vector_identificator.initialize()

    def requires_brainbox(self):
        return True





    