from .image_wrap import ImageWrap
from .image_list import ImageList
from pathlib import Path
from PIL import Image
import io
from brainbox import File

def _make_image(image) -> ImageWrap:
    if isinstance(image, Path) or isinstance(image, str):
        return ImageWrap(Image.open(image), Path(image).name)
    elif isinstance(image, bytes) or isinstance(image, bytearray):
        bts = io.BytesIO(image)
        return ImageWrap(Image.open(bts))
    elif isinstance(image, File):
        bts = io.BytesIO(image.content)
        return ImageWrap(Image.open(bts), image.name)
    elif isinstance(image, Image.Image):
        return ImageWrap(image)
    elif isinstance(image, ImageWrap):
        return ImageWrap(image.image, image.caption)
    else:
        raise TypeError(f"Unexpected type {type(image)}")


class ImgClass:
    def __call__(self, image) -> ImageWrap|ImageList:
        if isinstance(image, Path):
            if image.is_file():
                return _make_image(image)
            elif image.is_dir():
                return ImageList([_make_image(file) for file in Path(image).iterdir()])
            else:
                raise ValueError(f"Path {image} isneither file not directory.")
        if isinstance(image, list) or isinstance(image, tuple):
            return ImageList([_make_image(e) for e in image])
        elif isinstance(image, dict):
            result = []
            for key, value in image.items():
                _im = _make_image(value)
                _im.caption = key
                result.append(_im)
            return ImageList(result)
        elif isinstance(image, ImageList):
            return ImageList(image.images)
        else:
            return _make_image(image)

    def one(self, image) -> ImageWrap:
        return _make_image(image)

    def many(self, image) -> ImageList:
        result = self(image)
        if isinstance(result, ImageWrap):
            return ImageList([result])
        else:
            return result

Img = ImgClass()

