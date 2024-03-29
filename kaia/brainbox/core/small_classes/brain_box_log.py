from typing import *
from dataclasses import dataclass
from enum import Enum
from .decider_instance_dto import *

@dataclass
class LogItem:
    class Level(Enum):
        Service = 0
        Decider = 1
        Task = 2

    level: 'LogItem.Level'
    event: str
    id: Optional[str] = None

    def __str__(self):
        return f'{self.level.name} {self.event} {self.id}'

@dataclass
class _LogFactory1:
    callback: Optional[Callable]
    level: LogItem.Level
    _id: Optional[str]

    def event(self, s: str):
        if self.callback is not None:
            self.callback(LogItem(self.level, s, self._id))

@dataclass
class LogFactory:
    callback: Optional[Callable]

    def service(self):
        return _LogFactory1(self.callback, LogItem.Level.Service, None)

    def decider(self, name: DeciderInstanceSpec):
        return _LogFactory1(self.callback, LogItem.Level.Decider, str(name))

    def task(self, id: str):
        return _LogFactory1(self.callback, LogItem.Level.Task, id)
