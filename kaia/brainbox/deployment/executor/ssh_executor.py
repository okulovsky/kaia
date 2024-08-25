from typing import *
from .executor import IExecutor, Machine, Command
from .local_executor import LocalExecutor
import os
from pathlib import Path

class SSHExecutor(IExecutor):
    def __init__(self, machine: Machine):
        self.inner_executor = LocalExecutor()
        self.machine = machine


    def _get_prefix(self):
        return [
            'ssh',
            f'{self.machine.username}@{self.machine.ip_address}'
        ]

    def fix(self, s: Iterable[str]):
        return [ss.replace('\\','/') for ss in s]


    def upload_file(self, local_path: Path, remote_path: str):
        self.create_empty_folder(os.path.dirname(remote_path))
        self.inner_executor.execute(self.fix(['scp', str(local_path), f'{self.machine.username}@{self.machine.ip_address}:{remote_path}']))

    def download_file(self, remote_path: str, local_path: Path):
        os.makedirs(local_path.parent, exist_ok=True)
        self.inner_executor.execute(self.fix(['scp', f'{self.machine.username}@{self.machine.ip_address}:{remote_path}', str(local_path)]))


    def create_empty_folder(self, path: str|Path):
        self.inner_executor.execute(self.fix(self._get_prefix() + ['mkdir', '-p', str(path)]))

    def execute_command(self, command: Command):
        _command = self._get_prefix() + list(command.command)
        _command = self.fix(_command)
        return self.inner_executor.execute(_command, command.options)

    def delete_file_or_folder(self, remote_path: str):
        raise NotImplementedError("")

    def is_file(self, remote_path: str):
        result = self.inner_executor.execute(self._get_prefix()+['test', '-f', remote_path, '&&', 'echo', 'yes', '||', 'echo', 'no'], Command.Options(return_output=True))
        return result==b'yes\n'

    def is_dir(self, remote_path: str):
        result = self.inner_executor.execute(self._get_prefix()+['test', '-d', remote_path, '&&', 'echo', 'yes', '||', 'echo', 'no'], Command.Options(return_output=True))
        return result==b'yes\n'



    def get_machine(self) -> Machine:
        return self.machine