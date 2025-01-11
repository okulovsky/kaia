from typing import *
from .image_source import IImageSource
from .. import IExecutor


class DockerIOImageSource(IImageSource):
    def __init__(self,
                 name: str,
                 docker_url: str,
                 login: str,
                 password: str):
        self.name = name
        self.docker_url = docker_url
        self.login = login
        self.password = password

    def _auth_command(self) -> list:
        return ['docker', 'login', self.docker_url, '--username', self.login, '--password', self.password]

    def get_image_name(self):
        return self.name

    def get_remote_name(self):
        return f'{self.docker_url}/{self.name}:latest'

    def push(self, executor: IExecutor):
        executor.execute(['docker', 'tag', self.name, self.get_remote_name()])
        executor.execute(self._auth_command())
        executor.execute(['docker', 'push', self.get_remote_name()])

    def pull(self, executor: IExecutor):
        executor.execute(self._auth_command())
        executor.execute(['docker', 'pull', self.get_remote_name()])
        executor.execute(['docker', 'tag', self.get_remote_name(), self.name])







