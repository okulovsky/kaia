from abc import ABC, abstractmethod

class IStep(ABC):
    @abstractmethod
    def process(self, history, current):
        pass

    def shorten(self, data):
        return data

    def summarize(self, data) -> str|None:
        return None

    def get_name(self) -> str|None:
        if not hasattr(self,'_name'):
            return None
        return self._name

    def with_name(self, name: str) -> 'IStep':
        self._name = name
        return self


class IStepFactory(ABC):
    @abstractmethod
    def create_step(self) -> IStep:
        pass
