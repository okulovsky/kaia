import io

import PIL.Image
from pathlib import Path
import ipywidgets
import base64

class ConvertImage:
    def __init__(self, image:Path|str|bytes|PIL.Image.Image):
        if isinstance(image, Path) or isinstance(image, str):
            self.image = PIL.Image.open(image)
        elif isinstance(image, bytes):
            bts = io.BytesIO(image)
            self.image = PIL.Image.open(bts)
        else:
            self.image = image

    def resize_to_bounding(self, bounding_width: int, bounding_height: int|None = None):
        if bounding_height is None:
            bounding_height = bounding_width
        ratio_w = bounding_width / self.image.width
        ratio_h = bounding_height / self.image.height
        ratio = min(ratio_w, ratio_h)
        new_image = self.image.resize((int(ratio * self.image.width), int(ratio * self.image.height)))
        return ConvertImage(new_image)

    def resize_to_exact(self, width: int, height:int):
        new_image = self.image.resize((width, height))
        return ConvertImage(new_image)

    def _to_bytes(self) -> bytes:
        bio = io.BytesIO()
        self.image.save(bio, 'PNG')
        return bio.getvalue()

    def to_bytes(self) -> bytes:
        return self._to_bytes()

    def to_pywidget(self):
        return ipywidgets.Image(value=self._to_bytes())

    def to_base64(self) -> str:
        return base64.b64encode(self.to_bytes()).decode('utf-8')

    def to_html_tag(self) -> str:
        return f'<img src="data:image/png;base64, {self.to_base64()}"/>'

    def to_pil(self):
        return self.image