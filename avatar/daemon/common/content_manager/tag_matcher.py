from typing import Any
from abc import ABC, abstractmethod
from dataclasses import dataclass

class ITagMatcher(ABC):
    @abstractmethod
    def match(self, tags: dict[str, Any]) -> bool:
        pass


@dataclass
class TagMatcher(ITagMatcher):
    strong: bool
    tags: dict[str, Any]

    def match(self, tags: dict[str, Any]) -> bool:
        for key, value in self.tags.items():
            if key not in tags:
                if self.strong:
                    return False
                continue
            if value != tags[key]:
                return False
        return True

