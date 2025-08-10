from typing import *
from ....messaging import IMessage
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import base64

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
    base_64: str
    metadata: Any = None
    file_id: str|None = None

    @staticmethod
    def from_file(path: str | Path) -> "ImageCommand":
        path = Path(path)
        with path.open("rb") as f:
            data = f.read()
            encoded = base64.b64encode(data).decode("utf-8")
        return ImageCommand(base_64=encoded, metadata={"path": str(path)})



@dataclass
class SoundInjectionCommand(IMessage):
    file_id: str



@dataclass
class VolumeCommand(IMessage):
    value: float


@dataclass
class OpenMicCommand(IMessage):
    pass


@dataclass
class InitializationEvent(IMessage):
    pass