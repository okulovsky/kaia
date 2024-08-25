from typing import *
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from .machine import Machine
from .command import Command
from kaia.eaglesong import Automaton

class IExecutor(ABC):
    @abstractmethod
    def execute_command(self, command: Command):
        pass


    @abstractmethod
    def upload_file(self, local_path: Path, remote_path: str):
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path):
        pass

    @abstractmethod
    def create_empty_folder(self, path: str|Path):
        pass

    @abstractmethod
    def get_machine(self) -> Machine:
        pass

    @abstractmethod
    def is_file(self, remote_path: str):
        pass

    @abstractmethod
    def is_dir(self, remote_path: str):
        pass

    @abstractmethod
    def delete_file_or_folder(self, remote_path: str):
        pass

    def execute(self,
                commands: Union[Command.Acceptable, Iterable[Command.Acceptable], Command],
                options: Command.Options|None = None
                ):
        if isinstance(commands, Command):
            return self.execute_command(commands)
        commands = list(commands)
        as_one_command = Command.convert(commands)
        if as_one_command is not None:
            as_one_command.options = options
            return self.execute_command(as_one_command)
        else:
            ret_value = None
            for index, command in enumerate(commands):
                command_to_execute = Command.convert(command)
                if command_to_execute is None:
                    raise ValueError(f"Error at command #{index}: not acceptable {command}")
                command_to_execute.options = options
                ret_value = self.execute_command(command_to_execute)
            return ret_value


