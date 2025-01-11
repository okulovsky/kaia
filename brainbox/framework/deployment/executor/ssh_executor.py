from typing import *
from .executor import IExecutor, Command
from .file_system import IFileSystem
from .local_executor import LocalExecutor
import os
from pathlib import Path
from .ssh_file_system import SSHFileSystem
from .machine import Machine

class SSHExecutor(IExecutor):
    def __init__(self,  machine: Machine):
        self.inner_executor = LocalExecutor()
        self.machine = machine


    def _get_prefix(self):
        return [
            'ssh',
            f'{self.machine.username}@{self.machine.ip_address}'
        ]

    def fix(self, s: Iterable[str]):
        return [ss.replace('\\','/') for ss in s]


    def execute_command(self, command: Command):
        _command = self._get_prefix() + list(command.command)
        _command = self.fix(_command)
        return self.inner_executor.execute(_command, command.options)

    def get_fs(self) -> IFileSystem:
        return SSHFileSystem(self.machine)

    def get_machine(self) -> Machine:
        return self.machine






