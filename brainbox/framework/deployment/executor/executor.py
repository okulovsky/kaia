from typing import *
from abc import ABC, abstractmethod
from .command import Command
from pathlib import Path
from .file_system import IFileSystem
from .machine import Machine

class IExecutor(ABC):
    @abstractmethod
    def execute_command(self, command: Command):
        pass

    @abstractmethod
    def get_fs(self) -> IFileSystem:
        pass

    @abstractmethod
    def get_machine(self) -> Machine:
        return Machine.local()


    def execute(self,
                command: Command|Iterable[Union[str,Path]],
                options: Command.Options|None = None
                ):
        if isinstance(command, Command):
            return self.execute_command(command)
        command = Command(tuple(command), options)
        return self.execute_command(command)



