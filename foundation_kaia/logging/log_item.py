from abc import ABC, abstractmethod


class ILogItem(ABC):
    @abstractmethod
    def to_string(self) -> str:
        pass

    def to_html(self) -> str:
        return self.to_string()


