from dataclasses import dataclass
from typing import Any

@dataclass
class ButtonGridElement:
    text: str
    row: int
    column: int
    button_feedback: Any = None
    row_span: int|None = None
    column_span: int|None = None


@dataclass
class ButtonGrid:
    elements: tuple[ButtonGridElement,...]


@dataclass
class ButtonPressedEvent:
    button_feedback: Any