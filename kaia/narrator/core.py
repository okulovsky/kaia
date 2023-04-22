from typing import *
from dataclasses import dataclass, field
from enum import Enum

@dataclass
class NarrationHistoryItem:
    from_bot: True
    author: str
    message: Any

@dataclass
class NarrationStage:
    user: Optional[str] = None
    bot: Optional[str] = None
    history: List[NarrationHistoryItem] = field(default_factory=lambda: [])





@dataclass
class NarrationCommand:
    class Type(Enum):
        Improvise = 0
        Answer = 1

    type: 'NarrationCommand.Type'
    query: str
    stage: Optional[NarrationStage] = None

    def as_plain_text(self):
        return f"[{self.type.name}] {self.query}"

    @staticmethod
    def improvise(text: str, stage: Optional[NarrationStage] = None):
        return NarrationCommand(NarrationCommand.Type.Improvise, text, stage)

    @staticmethod
    def answer(text: str, stage: Optional[NarrationStage] = None):
        return NarrationCommand(NarrationCommand.Type.Answer, text, stage)

    def __eq__(self, other):
        if not isinstance(other, NarrationCommand):
            return False
        return self.query == other.query and self.type == other.type


class Narrator:
    def __init__(self, stage: NarrationStage):
        self.stage = stage

    def improvise(self, input: str):
        return NarrationCommand(NarrationCommand.Type.Improvise, input, self.stage)

    def answer(self, input: str):
        return NarrationCommand(NarrationCommand.Type.Answer, input, self.stage)