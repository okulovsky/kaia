from typing import *
from enum import Enum
from dataclasses import dataclass

@dataclass
class DubbingFragment:
    dub: str
    text: str
    is_placeholder: bool

    option_index: Optional[int] = -1
    file_name: Optional[str] = None
    voice: Optional[str] = None
    prefix: str = ''
    suffix: str = ''

    @property
    def full_text(self):
        return self.prefix+self.text+self.suffix


@dataclass
class DubbingSequence:
    fragments: Tuple[DubbingFragment,...]

    def get_text(self):
        return ''.join(c.prefix+c.text+c.suffix for c in self.fragments)



@dataclass
class FragmenterSettings:
    max_values_to_go_inline: int = 5
    min_set_values_to_break_to_words = 20
    set_dub_opening = 'Orange, '
    set_dub_closing = 'apple. '
    set_dub_prefix = ''
    set_dub_suffix = ', '
    max_sequence_length = 60
    min_sequence_length = 20



@dataclass
class CutSpec:
    start: int
    length: int
    info: DubbingFragment

@dataclass
class DubAndCutTask:
    cuts: List[CutSpec]
    text: str
    voice: str