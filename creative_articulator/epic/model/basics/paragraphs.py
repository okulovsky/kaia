from typing import ClassVar, Iterable
from dataclasses import dataclass
from .simhash import simhash
from enum import Enum

class ParagraphType(Enum):
    Plan = 'plan'
    Plain = 'plain'
    Dialog = 'dialog'
    Separator = 'separator'
    Blank = 'blank'
    Header = 'header'


@dataclass(frozen=True)
class Paragraph:
    content: str
    text_type: ParagraphType

    Type: ClassVar = ParagraphType

    @property
    def text(self) -> str:
        return self.content + '\n'

    @property
    def indent(self) -> int:
        return len(self.content) - len(self.content.lstrip(' '))

    @property
    def header_level(self) -> int:
        if self.text_type != ParagraphType.Header:
            return 0
        content = self.content.lstrip()
        return len(content) - len(content.lstrip('#'))

    @property
    def title(self) -> str:
        return self.content.strip().lstrip('#').strip()


# It has to be frozen, so, tuple, not list
class ParagraphArray(tuple[Paragraph, ...]):
    def __new__(cls, *paragraphs: Paragraph):
        return super().__new__(cls, paragraphs)

    def __init__(self, *paragraphs: Paragraph):
        self.simhash = simhash(e.content for e in self) #compute once and carry then

    @staticmethod
    def parse(text: str) -> 'ParagraphArray':
        return ParagraphArray(*(Paragraph(line, _classify(line)) for line in text.split('\n')))

    @staticmethod
    def join(arrays: Iterable['ParagraphArray']) -> 'ParagraphArray':
        paragraphs = []
        for array in arrays:
            paragraphs.extend(array)
        return ParagraphArray(*paragraphs)

    def subarray(self, start: int, stop: int) -> 'ParagraphArray':
        return ParagraphArray(*self[start:stop])

    @property
    def text(self) -> str:
        return '\n'.join(paragraph.content for paragraph in self)

    @property
    def length(self) -> int:
        return sum(len(paragraph.text) for paragraph in self)

    def has_type(self, text_type: ParagraphType) -> bool:
        return any(paragraph.text_type == text_type for paragraph in self)


_DIALOG_PREFIXES = ('-', '–', '—')


def _is_blank(line: str) -> bool:
    return line.strip() == ''


def _is_separator(line: str) -> bool:
    return line.strip() == '***'


def _is_header(line: str) -> bool:
    return line.startswith('#')


def _is_plan(line: str) -> bool:
    return line.startswith(' ')


def _is_dialog(line: str) -> bool:
    return line.lstrip().startswith(_DIALOG_PREFIXES)


def _classify(line: str) -> ParagraphType:
    if _is_separator(line):
        return ParagraphType.Separator
    if _is_blank(line):
        return ParagraphType.Blank
    if _is_header(line):
        return ParagraphType.Header
    if _is_plan(line):
        return ParagraphType.Plan
    if _is_dialog(line):
        return ParagraphType.Dialog
    return ParagraphType.Plain
