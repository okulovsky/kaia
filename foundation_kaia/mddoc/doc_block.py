from abc import ABC, abstractmethod
from typing import Any

class IDockBlock(ABC):
    @abstractmethod
    def to_md(self) -> str:
        pass

    @abstractmethod
    def get_lines(self) -> list[str]:
        pass

class TextBlock(IDockBlock):
    def __init__(self, lines: list[str]):
        self.lines = lines

    def get_lines(self) -> list[str]:
        return self.lines

    def to_md(self) -> str:
        return "\n".join(self.lines)

class ExpectedValueBlock(IDockBlock):
    def __init__(self, line: str, variable_value: Any):
        self.line = line
        self.variable_value = variable_value

    def get_lines(self) -> list[str]:
        return [self.line]

    def to_md(self) -> str:
        import pprint
        return pprint.pformat(self.variable_value)

