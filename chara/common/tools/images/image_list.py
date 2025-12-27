from typing import Iterable, Iterator

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

    def __getitem__(self, index: int) -> ImageWrap:
        return self.images[index]

    def __len__(self) -> int:
        return len(self.images)

    def __iter__(self) -> Iterator[ImageWrap]:
        return iter(self.images)

    def clone_for_other_set(self, other_set: Iterable[IDrawable]) -> 'IDrawableCollection':
        return ImageList(list(other_set))