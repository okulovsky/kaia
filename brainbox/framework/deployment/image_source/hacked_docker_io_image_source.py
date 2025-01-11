from .docker_io_image_source import DockerIOImageSource

class HackedDockerIOImageSource(DockerIOImageSource):
    def __init__(self,
                 name: str,
                 docker_url: str,
                 registry: str,
                 login: str,
                 password: str,
                 ):
        self.registry = registry
        super().__init__(name, docker_url, login, password)

    def get_remote_name(self) -> str:
        return f'{self.docker_url}/{self.registry}:{self.name}'

