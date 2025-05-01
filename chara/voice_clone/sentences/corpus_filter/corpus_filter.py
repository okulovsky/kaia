from abc import ABC, abstractmethod

class ICorpusFilter(ABC):
    @abstractmethod
    def filter(self, s: str) -> str|None:
        pass