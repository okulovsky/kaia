from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar('T')

@dataclass
class BrainboxReportItem(Generic[T]):
    log: str|None = None
    progress: float|None = None
    result: T|None = None