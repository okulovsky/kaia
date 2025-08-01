from .common import AvatarService, message_handler, PlayableTextMessage, State, ChatCommand, UtteranceEvent, TextEvent
from grammatron import DubParameters
from typing import *

class ChatService(AvatarService):
    def __init__(self,
                 state: State,
                 sender_to_image_url_translator: Callable[[str], str]
                 ):
        self.state = state
        self.sender_to_image_url_translator = sender_to_image_url_translator

    def requires_brainbox(self):
        return False

    def _get_picture(self, sender):
        if self.sender_to_image_url_translator is None:
            return None
        return self.sender_to_image_url_translator(sender)


    @message_handler
    def handle_to_user(self, message: PlayableTextMessage) -> ChatCommand:
        return ChatCommand(
            message.text.get_text(False, self.state.language),
            ChatCommand.MessageType.to_user,
            message.info.speaker,
            self._get_picture(message.info.speaker)
        )

    def _get_message_from_user(self, text):
        return ChatCommand(
            text,
            ChatCommand.MessageType.from_user,
            self.state.user,
            self._get_picture(self.state.user)
        )

    @message_handler
    def handle_from_user(self, message: UtteranceEvent):
        return self._get_message_from_user(message.utterance.to_str(DubParameters(False, self.state.language)))

