from typing import *
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DeciderInstanceSpec:
    decider_name: str
    parameters: Optional[str]
    def __str__(self):
        return f'{self.decider_name}/{self.parameters}'
    def __hash__(self):
        return self.__str__().__hash__()

@dataclass
class DeciderState:
    spec: DeciderInstanceSpec
    up: bool = False
    busy: bool = False
    not_busy_since: Optional[datetime] = None