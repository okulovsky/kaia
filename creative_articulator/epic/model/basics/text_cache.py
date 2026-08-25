from .paragraphs import ParagraphArray
from datetime import datetime, timezone
from dataclasses import dataclass

@dataclass
class TextCache:
    paragraphs: ParagraphArray
    updated: datetime

    def __post_init__(self):
        # The JSON cache round-trip (foundation_kaia serialization) has no
        # notion of tuple subclasses: it reconstructs `paragraphs` as a plain
        # list. Re-wrap here so every TextCache, freshly built or loaded from
        # cache, carries the real type and its precomputed simhash.
        if not isinstance(self.paragraphs, ParagraphArray):
            self.paragraphs = ParagraphArray(*self.paragraphs)
        # Every timestamp in the tree is timezone-aware UTC. Naive ones -
        # from datetime.now(), from caches written before this rule - are read
        # as local time and converted here, so no reader ever gets a mix and
        # the TypeError of comparing naive against aware can't happen.
        self.updated = self.updated.astimezone(timezone.utc)

    @property
    def text(self) -> str:
        return self.paragraphs.text

    @staticmethod
    def from_text(text: str, updated: datetime) -> 'TextCache':
        return TextCache(ParagraphArray.parse(text), updated)
