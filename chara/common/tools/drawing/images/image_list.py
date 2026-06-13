from .image_wrap import ImageWrap
from dataclasses import dataclass
from ..core import IDrawableCollection
from collections.abc import Iterator


@dataclass
class ImageList(IDrawableCollection[ImageWrap]):
    images: list[ImageWrap]

    def __iter__(self) -> Iterator[ImageWrap]:
        yield from self.images

    def __add__(self, other: 'ImageList') -> 'ImageList':
        return ImageList(self.images + other.images)

    def __getitem__(self, index: int) -> ImageWrap:
        return self.images[index]

    def __len__(self) -> int:
        return len(self.images)

    def resize(self, width_or_bbox: int, height: int|None = None) -> 'ImageList':
        return ImageList([i.resize(width_or_bbox, height) for i in self.images])