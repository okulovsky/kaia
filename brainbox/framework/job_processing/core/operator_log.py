from typing import *
from dataclasses import dataclass, field
from enum import Enum
from .decider_instance_key import DeciderInstanceKey
from datetime import datetime

@dataclass
class OperatorLogItem:
    class Level(Enum):
        Service = 0
        Decider = 1
        Task = 2
        Core = 3
        Planer = 4

    level: 'OperatorLogItem.Level'
    event: str
    id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self):
        id_width = 35  # Fixed width for id
        level_width = 10  # Fixed width for type

        id = ''
        if self.id is not None:
            id = self.id

        level = ''
        if self.level is not None:
            level = self.level.name
        details = f"{level:<{level_width}} {id:<{id_width}}  {self.event}"

        return details

@dataclass
class OperatorLogHandle:
    callback: Optional[Callable]
    level: OperatorLogItem.Level
    _id: Optional[str]

    def event(self, s: str):
        if self.callback is not None:
            self.callback(OperatorLogItem(self.level, s, self._id))

    def error(self, traceback: str, error_message='Error'):
        if self.callback is not None:
            self.callback(OperatorLogItem(self.level, error_message, self._id, traceback))

@dataclass
class OperatorLog:
    debug_output: bool = False
    log_items: list[OperatorLogItem] = field(default_factory = list)

    def _append(self, item):
        if self.debug_output:
            print(item)
        self.log_items.append(item)
        if len(self.log_items) > 5000:
            self.log_items = self.log_items[2500:]

    def service(self):
        return OperatorLogHandle(self._append, OperatorLogItem.Level.Service, None)

    def decider(self, name: DeciderInstanceKey):
        return OperatorLogHandle(self._append, OperatorLogItem.Level.Decider, str(name))

    def task(self, id: str):
        return OperatorLogHandle(self._append, OperatorLogItem.Level.Task, id)

    def core(self):
        return OperatorLogHandle(self._append, OperatorLogItem.Level.Core, None)

    def planer(self):
        return OperatorLogHandle(self._append, OperatorLogItem.Level.Planer, None)


