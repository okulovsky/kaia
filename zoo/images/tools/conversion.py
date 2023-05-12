from typing import *

import ipywidgets
from PIL import Image
from pathlib import Path
import base64
from io import BytesIO
import ipywidgets as widgets


class ConvertImage:
    def __init__(self, image: Union[Path, str, Image.Image]):
        self._image = image
        self._resize = None

    def resize(self, width, height) -> 'ConvertImage':
        self._resize = (width, height)
        return self

    def _to_bytearray(self, image) -> bytearray:
        if not isinstance(image,Image.Image):
            image = Image.open(image)
        else:
            image = image
        if self._resize is not None:
            image = image.resize(self._resize)
        bio = BytesIO()
        image.save(bio, 'PNG')
        return bio.getvalue()


    def to_bytearray(self) -> bytearray:
        return self._to_bytearray(self._image)

    def _to_pywidget_image(self, image):
        return widgets.Image(value=self._to_bytearray(image))

    def to_pywidget(self) -> widgets.Widget:
        if isinstance(self._image, list):
            if isinstance(self._image[0], list):
                return ipywidgets.VBox([
                    ipywidgets.HBox([
                        self._to_pywidget_image(im) for im in row
                    ])
                    for row in self._image
                    ])
            else:
                return ipywidgets.HBox([self._to_pywidget_image(im) for im in self._image])
        else:
            return self._to_pywidget_image(self._image)

    def to_base64(self) -> str:
        return base64.b64encode(self.to_bytearray()).decode('utf-8')

    @staticmethod
    def from_base64(str):
        return Image.open(BytesIO(base64.decodebytes(bytes(str, "utf-8"))))