from .common import message_handler, AvatarService, State, SoundEvent, CommandConfirmationQueue, UtteranceEvent, TextEvent
from .stt_service import STTService
from grammatron import Utterance

class STTIntegrationService(AvatarService):
    def __init__(self, state: State):
        self.state = state

    @message_handler
    def on_sound_event(self, event: SoundEvent):
        command = STTService.Command(
            file = event.file_id,
            language = self.state.language
        ).as_reply_to(event)
        result = self.client.run_synchronously(command, STTService.Confirmation)
        if isinstance(result.recognition, Utterance):
            yield UtteranceEvent(result.recognition).as_reply_to(result)
        elif isinstance(result.recognition, str):
            yield TextEvent(result.recognition).as_reply_to(result)
        else:
            raise ValueError(f"STT returned recognition of type {type(result.recognition)}, which is not expected")

    def requires_brainbox(self):
        return True
