from typing import Iterable

from ..core import IDrawableCollection, IDrawable
from .image_wrap import ImageWrap
from dataclasses import dataclass

@dataclass
class ImageList(IDrawableCollection):
    images: list[ImageWrap]

    def get_drawables(self) -> Iterable[IDrawable]:
        return self.images

    def __add__(self, other: 'ImageList') -> 'ImageList':
        return ImageList(self.images + other.images)