from dataclasses import dataclass
from avatar.daemon import IMessage

@dataclass
class ChatConfirmation(IMessage):
    interrupted: bool

@dataclass
class ChangeMessageEvent(IMessage):
    message_id: str
    delta: int


@dataclass
class SwipeChatMessageEvent(IMessage):
    message_id: str
    swipe_to_left: bool

@dataclass
class DeleteChatMessagesCommand(IMessage):
    ids: list[str]

@dataclass
class DeleteChatMessageEvent(IMessage):
    message_id: str