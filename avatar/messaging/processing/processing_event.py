from ..stream import IMessage
from ..rules import Rule
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum

class ProcessingEventType(Enum):
    Received = 0
    Accepted = 1
    Finished = 2
    Error = 3
    Started = 4


@dataclass
class ProcessingEvent:
    type: ProcessingEventType
    message: IMessage
    rule: Rule|None = None
    raw_output: Any = None
    parsed_output: Any = None
    exception: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    Type = ProcessingEventType