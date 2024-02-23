from typing import *
from .container_pusher import ContainerPusher
import subprocess

class SimpleContainerPusher(ContainerPusher):
    def __init__(self, docker_url, registry, login, password):
        self.registry = registry
        self.docker_url = docker_url
        self.login = login
        self.password = password

    def _try_execute(self, arguments):
        if subprocess.call(list(arguments)) != 0:
            raise ValueError(f'Error when running command\n{" ".join(arguments)}')


    def get_auth_command(self) -> Iterable[str]:
        return ['docker', 'login', self.docker_url, '--username', self.login, '--password',
                self.password]


    def push(self, image_name: str, image_tag: str):
        self._try_execute(['docker','tag',f'{self.registry}:{image_tag}',f'{self.docker_url}/{self.registry}:latest'])
        self._try_execute(self.get_auth_command())
        self._try_execute(['docker','push',f'{self.docker_url}/{self.registry}:latest'])

