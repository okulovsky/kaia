from typing import *
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

class AutomatonExit(Exception):
    pass

class Return(AutomatonExit):
    def __init__(self, value = None):
        self.value = value

@dataclass
class Terminate(AutomatonExit):
    message: str

T = TypeVar('T')

class Listen:
    def __init__(self):
        self._payload: dict[Type, Any] = {}

    def __getitem__(self, type: Type[T]) -> T:
        return self._payload[type]

    def store(self, value: Any) -> 'Listen':
        self._payload[type(value)] = value
        return self

    def get(self, type: Type):
        return self._payload[type]

    def __contains__(self, item: Type):
        return item in self._payload

