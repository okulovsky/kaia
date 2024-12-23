from .image_source import IImageSource
from ..executor import IExecutor, Command


class LocalImageSource(IImageSource):
    def __init__(self, image_name: str):
        self.image_name = image_name

    def get_image_name(self):
        return self.image_name

    def get_container_name(self):
        return self.image_name

    def pull(self, executor: IExecutor):
        pass

    def push(self, executor: IExecutor):
        pass






