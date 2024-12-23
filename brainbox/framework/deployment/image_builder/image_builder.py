from abc import ABC, abstractmethod
from ..executor import IExecutor

class IImageBuilder(ABC):
    @abstractmethod
    def build_image(self, image_name: str, exec: IExecutor) -> None:
        pass


