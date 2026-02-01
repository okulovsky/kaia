from .common import message_handler, AvatarService, InternalTextCommand, State, Confirmation
from .tts_service import TTSService
import re


def simple_sent_tokenize(text: str) -> list[str]:
    """
    Splits text into sentences in a simplified way, similar to nltk.sent_tokenize,
    but without external dependencies.

    Limitations:
    - Does not handle all abbreviations correctly (e.g. "Dr.", "e.g.", etc.).
    - May split incorrectly in complex cases.
    """
    # This regex looks for '.', '!' or '?' followed by space and a capital letter
    # It uses a lookbehind to split but keeps the punctuation.
    sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-ZА-ЯЁ])')
    sentences = sentence_endings.split(text.strip())

    return [s.strip() for s in sentences if s.strip()]


class TTSIntegrationService(AvatarService):

    @message_handler.with_call(TTSService.Command)
    def on_playable_text(self, event: InternalTextCommand) -> Confirmation:
        text = event.get_text(True)
        sentences = simple_sent_tokenize(text)
        settings = TTSService.Command.Settings(event.character, event.language)
        command = TTSService.Command(tuple(sentences), settings).as_reply_to(event)
        result = self.client.run_synchronously(command)
        confirmation = event.confirm_this().as_reply_to(result)
        return confirmation

    def requires_brainbox(self):
        return True
