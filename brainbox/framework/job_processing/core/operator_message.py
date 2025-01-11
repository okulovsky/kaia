from typing import *
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

@dataclass
class OperatorMessage:
    class Type(Enum):
        accepted = 0
        report_progress = 1
        log = 2
        result = 3
        error = 4



    id: str
    type: 'OperatorMessage.Type'
    payload: Any = None
    timestamp: datetime = field(default_factory=datetime.now)

