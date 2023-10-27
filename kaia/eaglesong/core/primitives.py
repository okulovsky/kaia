from typing import *
from dataclasses import dataclass
from datetime import datetime

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
    pass

@dataclass
class Terminate(AutomatonExit):
    message: str

@dataclass
class Listen:
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
class Audio(IBotOutput, IBotInput):
    data: bytes
    text: str


