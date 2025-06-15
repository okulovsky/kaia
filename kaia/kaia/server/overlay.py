from dataclasses import dataclass
from typing import Any

@dataclass
class OverlayButton:
    text: str
    row: int
    column: int
    button_feedback: Any = None
    row_span: int|None = None
    column_span: int|None = None


class OverlayButtonGridBuilder:
    def __init__(self, column_count: int = 4):
        self.index = 0
        self.elements = []
        self.column_count = column_count

    def add(self, name: str, payload: Any):
        self.elements.append(OverlayButton(
            name,
            self.index // self.column_count,
            self.index % self.column_count,
            payload,
        ))
        self.index+=1

    def to_overlay(self):
        return Overlay(tuple(self.elements))


class Overlay:
    def __init__(self, elements: tuple[OverlayButton,...]|None = None):
        self.elements = elements

    Button = OverlayButton
    GridBuilder = OverlayButtonGridBuilder

    @staticmethod
    def remove():
        return Overlay()


@dataclass
class ButtonPressedEvent:
    button_feedback: Any