from typing import *
from abc import ABC, abstractmethod

class IContainerPusher(ABC):
    @abstractmethod
    def get_auth_command(self):
        pass

    @abstractmethod
    def get_push_command(self, local_image_name: str) -> Iterable[str|list[str]]:
        pass

    @abstractmethod
    def get_remote_name(self) -> str:
        pass

    @abstractmethod
    def get_ancestor(self) -> str:
        pass


    def get_pull_command(self) -> Iterable[str|list[str]]:
        return [
            self.get_auth_command(),
            ['docker', 'pull', self.get_remote_name()]
        ]


