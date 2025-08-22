from .common import AvatarService, message_handler, PlayableTextMessage, State, ChatCommand, UtteranceEvent, ExceptionEvent, TextEvent
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
    def on_utterance_event(self, message: UtteranceEvent) -> ChatCommand:
        return self._get_message_from_user(message.utterance.to_str(DubParameters(False, self.state.language)))


    @message_handler
    def on_text_event(self, message: TextEvent) -> ChatCommand:
        return self._get_message_from_user(message.text)


    @message_handler
    def handle_exception(self, message: ExceptionEvent) -> ChatCommand:
        return ChatCommand(
            f"Exception at {message.source}\n\n{message.traceback}",
            ChatCommand.MessageType.error,
        )

