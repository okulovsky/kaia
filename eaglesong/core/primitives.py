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
    def __init__(self, *payload: Any):
        self._payload = list(payload)

    def store(self, item) -> 'Listen':
        self._payload.append(item)
        return self

    def get_payload(self):
        return self._payload

