from abc import ABC, abstractmethod

class IContainerBuilder(ABC):
    @abstractmethod
    def get_local_name(self) -> str:
        pass


    @abstractmethod
    def build_container(self) -> None:
        pass


class FakeContainerBuilder(IContainerBuilder):
    def __init__(self, name: str):
        self.name = name

    def get_local_name(self) -> str:
        return self.name

    def build_container(self) -> None:
        pass
