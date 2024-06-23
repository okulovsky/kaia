from typing import *
from .executor import IExecutor, ExecuteOptions
from .local_executor import LocalExecutor
import os
from pathlib import Path

class SSHExecutor(IExecutor):
    def __init__(self,
                 ssh_url: str,
                 ssh_username: str,
                 ):
        self.ssh_url = ssh_url
        self.ssh_username = ssh_username
        self.inner_executor = LocalExecutor()


    def _get_prefix(self):
        return [
            'ssh',
            f'{self.ssh_username}@{self.ssh_url}'
        ]

    def fix(self, s: str| Iterable[str]):
        if isinstance(s, str):
            return s.replace('\\','/')
        return [self.fix(z) for z in s]


    def upload_file(self, local_path: Path, remote_path: str):
        self.create_empty_folder(os.path.dirname(remote_path))
        self.inner_executor.execute(self.fix(['scp', str(local_path), f'{self.ssh_username}@{self.ssh_url}:{remote_path}']))

    def download_file(self, remote_path: str, local_path: Path):
        self.inner_executor.execute(self.fix(['scp', f'{self.ssh_username}@{self.ssh_url}:{remote_path}', str(local_path)]))


    def create_empty_folder(self, path: str|Path):
        self.inner_executor.execute(self.fix(self._get_prefix() + ['mkdir', '-p', str(path)]))

    def execute(self, command: Iterable[str], options: ExecuteOptions|None = None):
        if isinstance(command, str):
            raise TypeError("`str` type for command is no longer supported. Use array of commands")
        else:
            command = self._get_prefix() + list(command)
        return self.inner_executor.execute(self.fix(command), options)