from typing import Any
from abc import ABC, abstractmethod
from dataclasses import dataclass

class ITagMatcher(ABC):
    @abstractmethod
    def match(self, tags: dict[str, Any]) -> str|None:
        pass


@dataclass
class TagMatcher(ITagMatcher):
    strong: bool
    tags: dict[str, Any]

    def match(self, tags: dict[str, Any]) -> str|None:
        for key, value in self.tags.items():
            actual = tags.get(key, None)
            if actual is None and not self.strong:
                # weak matching: the record is not opinionated about this tag, so it passes
                continue
            if value != actual:
                return f'{key}: exp {value}, act {actual}'
        return None

