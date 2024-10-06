from abc import ABC, abstractmethod
from .state import State

class InitialStateFactory(ABC):
    @abstractmethod
    def create(self, session_id: str):
        pass

    @staticmethod
    def Simple(state: dict[str, str]) -> 'SimpleInitialStateFactory':
        return SimpleInitialStateFactory(state)


class SimpleInitialStateFactory(InitialStateFactory):
    def __init__(self, state: dict[str, str]):
        self.state = state

    def create(self, session_id: str):
        return State(self.state)



