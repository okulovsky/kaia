from brainbox import BrainBox
from brainbox.deciders import Resemblyzer
from .common import SoundEvent, IMessage, message_handler, State, AvatarService, InitializationEvent
from .common.vector_identificator import VectorIdentificator, VectorIdentificatorSettings
from .brainbox_service import BrainBoxService
from dataclasses import dataclass
from pathlib import Path
from brainbox.framework import FileLike
from ..server import AvatarApi
from yo_fluq import FileIO

@dataclass
class SpeakerIdentificationTrain(IMessage):
    true_speaker: str

@dataclass
class SpeakerIdentificationTrainConfirmation(IMessage):
    admit_errors: bool



class SpeakerIdentificationService(AvatarService):
    Train = SpeakerIdentificationTrain
    TrainConfirmation = SpeakerIdentificationTrainConfirmation


    def __init__(self, state: State, settings: VectorIdentificatorSettings, api: AvatarApi):
        self.state = state
        self.vector_identificator = VectorIdentificator(settings, self.sample_to_vector, api.file_cache.download)
        self.buffer: list[tuple[SoundEvent,str]] = []


    def sample_to_vector(self, file: FileLike.Type):
        command = BrainBoxService.Command(
            BrainBox.Task
            .call(Resemblyzer).vector(file)
            .to_task()
        )
        return self.client.run_synchronously(command, BrainBoxService.Confirmation).result['vector']

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def on_sound_event(self, message: SoundEvent) -> None:
        speaker = self.vector_identificator.analyze(message.file_id)
        if speaker is not None:
            self.state.user = speaker
            self.buffer.append((message,speaker))
            self.buffer = self.buffer[-2:]

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def on_initialize(self, message: InitializationEvent):
        self.vector_identificator.initialize()

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def train(self, message: SpeakerIdentificationTrain) -> SpeakerIdentificationTrainConfirmation:
        count = 0
        for event, speaker in self.buffer:
            if speaker == message.true_speaker:
                continue
            self.vector_identificator.add_sample(message.true_speaker, event.file_id)
            count += 1

        if count == 0:
            return SpeakerIdentificationTrainConfirmation(False).as_confirmation_for(message)
        self.vector_identificator.initialize()
        return SpeakerIdentificationTrainConfirmation(True).as_confirmation_for(message)


    def requires_brainbox(self):
        return True





    