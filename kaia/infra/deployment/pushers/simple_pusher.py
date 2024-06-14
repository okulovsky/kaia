from typing import *
from .container_pusher import IContainerPusher

class SimpleContainerPusher(IContainerPusher):
    def __init__(self, docker_url, registry, login, password):
        self.registry = registry
        self.docker_url = docker_url
        self.login = login
        self.password = password

    def get_auth_command(self) -> Iterable[str]:
        return ['docker', 'login', self.docker_url, '--username', self.login, '--password',
                self.password]

    def get_remote_name(self) -> str:
        return f'{self.docker_url}/{self.registry}:latest'


    def get_push_command(self, local_image_name: str) -> Iterable[str|list[str]]:
        return [
            ['docker', 'tag', local_image_name, self.get_remote_name()],
            self.get_auth_command(),
            ['docker', 'push', self.get_remote_name()]
        ]

    def get_ancestor(self) -> str:
        return f'{self.docker_url}/{self.registry}'




