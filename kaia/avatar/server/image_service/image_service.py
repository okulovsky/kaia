from abc import ABC, abstractmethod
from ....eaglesong.core import Image


class IImageService(ABC):
    @abstractmethod
    def get_image(self, tags: dict[str, str]) -> Image | None:
        pass

    @abstractmethod
    def feedback(self, feedback: str) -> None:
        pass
