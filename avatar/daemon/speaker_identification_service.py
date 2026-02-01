from brainbox import BrainBox
from brainbox.deciders import Resemblyzer
from .common import SoundEvent, IMessage, message_handler, State, AvatarService, InitializationEvent
from .common.vector_identificator import VectorIdentificator, IStrategy
from .brainbox_service import BrainBoxService
from dataclasses import dataclass
from brainbox.framework import FileLike
from ..server import AvatarApi
from ..messaging import Confirmation


@dataclass
class SpeakerIdentificationTrain(IMessage):
    file_id: str
    actual_user: str

@dataclass
class SpeakerIdentificationCommand(IMessage):
    file_id: str



class SpeakerIdentificationService(AvatarService):
    Train = SpeakerIdentificationTrain
    Command = SpeakerIdentificationCommand

    def __init__(self,
                 api: AvatarApi,
                 identification_strategy: IStrategy,
                 ):
        self.api = api
        self.identification_strategy = identification_strategy

        self.buffer: list[tuple[SoundEvent,str]] = []
        self.vector_identificator: VectorIdentificator|None = None

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def on_initialize(self, message: InitializationEvent) -> None:
        self.vector_identificator = VectorIdentificator(
            self.resources_folder,
            self.identification_strategy,
            self.sample_to_vector,
            self.api.file_cache.open
        )
        self.vector_identificator.initialize()


    def sample_to_vector(self, file: FileLike.Type):
        command = BrainBoxService.Command(
            BrainBox.Task
            .call(Resemblyzer).vector(file)
            .to_task()
        )
        return self.client.run_synchronously(command, BrainBoxService.Confirmation).result['vector']

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def on_sound_event(self, message: SpeakerIdentificationCommand) -> Confirmation:
        speaker = self.vector_identificator.analyze(message.file_id)
        return Confirmation(speaker).as_confirmation_for(message)


    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def train(self, message: SpeakerIdentificationTrain) -> None:
        self.vector_identificator.add_sample(message.actual_user, message.file_id)
        self.vector_identificator.initialize()

    def requires_brainbox(self):
        return True





    