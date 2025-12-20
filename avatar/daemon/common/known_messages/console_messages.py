from typing import *
from ....messaging import IMessage
from dataclasses import dataclass
from enum import Enum

@dataclass
class SoundEvent(IMessage):
    file_id: str



@dataclass
class SoundCommand(IMessage):
    file_id: str
    text: str|None = None


@dataclass
class SoundConfirmation(IMessage):
    terminated: bool = False


@dataclass
class WakeWordEvent(IMessage):
    word: str|None = None

class ChatMessageType(Enum):
    from_user = 'from_user'
    to_user = 'to_user'
    system = 'system'
    error = 'error'


@dataclass
class ChatCommand(IMessage):
    text: str
    type: ChatMessageType = ChatMessageType.from_user
    sender_name: str|None = None
    sender_avatar_file_id: str|None = None

    MessageType = ChatMessageType

@dataclass
class ImageCommand(IMessage):
    file_id: str
    metadata: Any = None



@dataclass
class SoundInjectionCommand(IMessage):
    file_id: str



@dataclass
class VolumeCommand(IMessage):
    value: float


@dataclass
class VolumeEvent(IMessage):
    value: float


@dataclass
class OpenMicCommand(IMessage):
    pass


@dataclass
class InitializationEvent(IMessage):
    pass

@dataclass
class ImageEvent(IMessage):
    file_id: str