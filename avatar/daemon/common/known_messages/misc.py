from dataclasses import dataclass
from ....messaging import IMessage

@dataclass
class ErrorAnnouncement(IMessage):
    content: str|None = None