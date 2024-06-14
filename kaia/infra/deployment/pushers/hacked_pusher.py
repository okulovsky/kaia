from .simple_pusher import SimpleContainerPusher

class HackedContainerPusher(SimpleContainerPusher):
    def __init__(self, docker_url, registry, login, password, tag):
        super().__init__(docker_url, registry, login, password)
        self.tag = tag

    def get_remote_name(self) -> str:
        return f'{self.docker_url}/{self.registry}:{self.tag}'


    def get_ancestor(self) -> str:
        return f'{self.docker_url}/{self.registry}:{self.tag}'




