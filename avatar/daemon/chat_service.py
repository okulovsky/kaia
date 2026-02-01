from .common import AvatarService, message_handler, State, ChatCommand, ExceptionEvent, TextEvent, InternalTextCommand
from grammatron import DubParameters
from typing import *

class ChatService(AvatarService):
    def __init__(self,
                 sender_to_image_url_translator: Callable[[str], str]
                 ):
        self.sender_to_image_url_translator = sender_to_image_url_translator

    def requires_brainbox(self):
        return False

    def _get_picture(self, sender):
        if self.sender_to_image_url_translator is None:
            return None
        if sender is None:
            return None
        return self.sender_to_image_url_translator(sender)


    @message_handler
    def on_command(self, message: InternalTextCommand) -> ChatCommand:
        return ChatCommand(
            message.get_text(False),
            ChatCommand.MessageType.to_user,
            message.character,
            self._get_picture(message.character)
        )



    @message_handler
    def on_event(self, message: TextEvent) -> ChatCommand:
        return ChatCommand(
            message.get_text(False),
            ChatCommand.MessageType.from_user,
            message.user,
            self._get_picture(message.user)
        )

    @message_handler
    def handle_exception(self, message: ExceptionEvent) -> ChatCommand:
        return ChatCommand(
            f"Exception at {message.source}\n\n{message.traceback}",
            ChatCommand.MessageType.error,
        )

