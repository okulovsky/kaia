from typing import Any
from dataclasses import dataclass
from ..common import IMessage
from ..stt_service import IRecognitionRequest


@dataclass
class NLUTextEvent(IMessage):
    file_id: str
    text: str|None
    request: IRecognitionRequest
    error: Any = None
