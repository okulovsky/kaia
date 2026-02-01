from .common import message_handler, AvatarService, State, SoundEvent, CommandConfirmationQueue, TextEvent
from .stt_service import STTService
from .speaker_identification_service import SpeakerIdentificationService
from grammatron import Utterance
from ..messaging import Confirmation

class STTIntegrationService(AvatarService):
    def __init__(self,
                 state: State,
                 enable_speaker_identification: bool = False,
                 ):
        self.state = state
        self.enable_speaker_identification = enable_speaker_identification

    @message_handler.with_call(STTService.Command, STTService.Confirmation)
    def on_sound_event(self, event: SoundEvent) -> TextEvent:
        command = STTService.Command(
            file = event.file_id,
            language = self.state.language
        ).as_reply_to(event)
        self.client.put(command)

        if self.enable_speaker_identification:
            id_command = SpeakerIdentificationService.Command(event.file_id)
            speaker = self.client.run_synchronously(id_command, Confirmation).result
        else:
            speaker = None

        result = self.client.wait_for_confirmation(command, STTService.Confirmation)

        if not isinstance(result.recognition, (str, Utterance)):
            raise ValueError(f"STT returned recognition of type {type(result.recognition)}, which is not expected")
        else:
            return TextEvent(result.recognition, speaker, event.file_id).as_reply_to(result)


    def requires_brainbox(self):
        return True
