from typing import Any, TypeVar, Generic
from ...cases import ICase
from abc import ABC, abstractmethod
from pathlib import Path


class IAnnotationCase(ICase, ABC):
    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def set_annotation(self, annotation: Any):
        pass

TCase = TypeVar("TCase", bound=IAnnotationCase)


class IAnnotator(Generic[TCase], ABC):
    @abstractmethod
    def run(self, cases: list[TCase], folder: Path):
        pass

    @abstractmethod
    def get_result(self, folder: Path):
        pass



