from ..stream import IMessage
from ..rules import Rule
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum

class ProcessingEventType(Enum):
    Received = 0
    Rejected = 1
    Accepted = 2
    Finished = 3
    Error = 4
    Started = 5


@dataclass
class ProcessingEvent(IMessage):
    type: ProcessingEventType
    message: IMessage
    rule_name: str|None = None
    parsed_output: Any = None
    exception: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    rejection_reason: str|None = None

    Type = ProcessingEventType