from dataclasses import dataclass
from typing import Any
from ....messaging import IMessage

@dataclass
class Button:
    text: str
    row: int
    column: int
    button_feedback: Any = None
    row_span: int|None = None
    column_span: int|None = None


class ButtonGridBuilder:
    def __init__(self, column_count: int = 4):
        self.index = 0
        self.elements = []
        self.column_count = column_count

    def add(self, name: str, payload: Any) -> 'ButtonGridBuilder':
        self.elements.append(Button(
            name,
            self.index // self.column_count,
            self.index % self.column_count,
            payload,
        ))
        self.index+=1
        return self

    def to_grid(self):
        return ButtonGrid(tuple(self.elements))

@dataclass
class ButtonGrid(IMessage):
    elements: tuple[Button,...]|None = None


    Button = Button
    Builder = ButtonGridBuilder

    @staticmethod
    def empty():
        return ButtonGrid()


@dataclass
class ButtonPressedEvent(IMessage):
    button_feedback: Any