from typing import *
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ExecuteOptions:
    workdir: str|Path|None = None
    return_output: bool = False

class IExecutor(ABC):
    @abstractmethod
    def execute(self, command: str | Iterable[str], options: ExecuteOptions|None = None):
        pass

    def execute_several(self, commands: Iterable[str|Iterable[str]]):
        for command in commands:
            if len(command) == 0:
                continue
            self.execute(command)

    @abstractmethod
    def upload_file(self, local_path: Path, remote_path: str):
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path):
        pass

    @abstractmethod
    def create_empty_folder(self, path: str|Path):
        pass


    def argument_to_string(self, cmd: Union[str, Iterable[str]]) -> str:
        if isinstance(cmd, str):
            return cmd
        return ' '.join(cmd)
