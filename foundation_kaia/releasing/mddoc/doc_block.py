from abc import ABC, abstractmethod
from typing import Any


def strip_common_indent(lines: list[str]) -> list[str]:
    non_empty = [l for l in lines if l.strip() != '']
    if not non_empty:
        return []
    min_indent = min(len(l) - len(l.lstrip()) for l in non_empty)
    result = ['' if l.strip() == '' else l[min_indent:] for l in lines]
    while result and result[0] == '':
        result.pop(0)
    while result and result[-1] == '':
        result.pop()
    return result


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
        return "\n".join(strip_common_indent(self.lines))

class ExpectedValueBlock(IDockBlock):
    def __init__(self, line: str, variable_value: Any):
        self.line = line
        self.variable_value = variable_value

    def get_lines(self) -> list[str]:
        return [self.line]

    def to_md(self) -> str:
        import pprint
        return '```\n' + pprint.pformat(self.variable_value) + '\n```'

