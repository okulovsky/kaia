from dataclasses import dataclass
from ....messaging import IMessage

@dataclass
class ErrorAnnouncement(IMessage):
    content: str|None = None

@dataclass
class ServerStartedEvent(IMessage):
    pass