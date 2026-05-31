from dataclasses import dataclass
from chara.common import ICase


@dataclass
class NegativeCase(ICase):
    language: str
    batch_index: int
    phrase: str | None = None
