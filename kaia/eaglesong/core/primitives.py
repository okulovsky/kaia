from typing import *
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

@dataclass
class BotContext:
    user_id: Any
    input: Any = None
    timestamp: Optional[datetime] = None


class IBotInput:
    pass

@dataclass
class SelectedOption(IBotInput):
    value: Any


@dataclass
class TimerTick(IBotInput):
    pass


class AutomatonExit(Exception):
    pass


class Return(AutomatonExit):
    def __init__(self, value = None):
        self.value = value

@dataclass
class Terminate(AutomatonExit):
    message: str

@dataclass
class Listen:
    pass


@dataclass
class Empty:
    pass

class IBotOutput:
    pass

@dataclass
class Delete(IBotOutput):
    id: Any


@dataclass
class Options(IBotOutput):
    content: Any
    options: Tuple[Any,...]



@dataclass
class Media(ABC, IBotOutput, IBotInput):
    class Type(Enum):
        Audio = 0
        Image = 1

    data: bytes
    text: Optional[str]
    id: Optional[str]

    @property
    @abstractmethod
    def type(self):
        pass




class Audio(Media):
    def __init__(self, data: bytes, text: Optional[str] = None, id: Optional[str] = None):
        super().__init__(data, text, id)

    def type(self):
        return Media.Type.Audio

    @staticmethod
    def from_file(filename, text: Optional[str] = None):
        with open(filename,'rb') as file:
            data = file.read()
        return Audio(data, text, str(filename))

class Image(Media):
    def __init__(self, data: bytes, text: Optional[str] = None, id: Optional[str] = None):
        super().__init__(data, text, id)


    def type(self):
        return Media.Type.Image





