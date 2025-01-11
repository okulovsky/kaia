from .image_source import IImageSource
from .. import IExecutor


class RemotePublicImageSource(IImageSource):
    def __init__(self, remote_image_name, container_name):
        self.image_name = remote_image_name
        self.container_name = container_name

    def get_image_name(self):
        return self.image_name

    def push(self, executor: IExecutor):
        pass

    def pull(self, executor: IExecutor):
        executor.execute(['docker', 'pull', self.image_name])

    def get_container_name(self):
        return self.container_name


