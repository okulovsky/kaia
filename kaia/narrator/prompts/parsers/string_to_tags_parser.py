from abc import ABC, abstractmethod

class IStringToTagsParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> list[dict]:
        pass