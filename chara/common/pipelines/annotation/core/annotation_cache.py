from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class AnnotationStatus:
    value: Any | None = None
    skipped_times: int = 0

    @property
    def annotated(self) -> bool:
        return self.value is not None


class IAnnotationCache(ABC):
    @abstractmethod
    def get_annotation_status(self) -> dict[str, AnnotationStatus]:
        pass

    @abstractmethod
    def get_summary(self) -> str:
        pass

    @abstractmethod
    def finish_annotation(self):
        pass

    @abstractmethod
    def undo(self):
        pass