from .common import message_handler, AvatarService, PlayableTextMessage, State
from .tts_service import TTSService
from grammatron import Utterance
import nltk
from nltk.tokenize import sent_tokenize

class TTSIntegrationService(AvatarService):
    def __init__(self):
        try:
            sent_tokenize('Text. Text')
        except:
            nltk.download('punkt')

    @message_handler
    def on_playable_text(self, event: PlayableTextMessage):
        text = event.text.get_text(True, event.info.language)
        sentences = sent_tokenize(text)
        command = TTSService.Command(tuple(sentences), event.info).as_reply_to(event)
        result = self.client.run_synchronously(command)
        confirmation = event.confirm_this().as_reply_to(result)
        return confirmation

    def requires_brainbox(self):
        return True
