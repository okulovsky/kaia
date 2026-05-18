from abc import ABC, abstractmethod
from pathlib import Path


class ResultType(ABC):
    @abstractmethod
    def get_extension(self) -> str:
        pass

    @abstractmethod
    def accepts_data(self, data) -> bool:
        pass

    @abstractmethod
    def write(self, data, path: Path):
        pass

    @abstractmethod
    def read(self, path: Path):
        pass

    @staticmethod
    def get_all_types() -> 'tuple[ResultType,...]':
        from .all_types import get_all_result_types
        return get_all_result_types()

    @staticmethod
    def find_type(types: 'tuple[ResultType,...]', data) -> 'ResultType':
        for t in types:
            if t.accepts_data(data):
                return t
        raise ValueError(f"Cannot find a type for {type(data)}")