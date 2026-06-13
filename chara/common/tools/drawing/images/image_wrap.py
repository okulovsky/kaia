import ipywidgets
from PIL import Image
from dataclasses import dataclass
import io
import base64
from ..core import IDrawable
from copy import copy

@dataclass
class ImageWrap(IDrawable):
    image: Image.Image
    caption: str | None = None

    def replace_image(self, new_image: Image.Image):
        result = ImageWrap(image=new_image, caption=self.caption)
        if hasattr(self, '_metadata'):
            result._metadata = copy(self._metadata)
        return result

    def _to_bytes(self) -> bytes:
        bio = io.BytesIO()
        self.image.save(bio, 'PNG')
        return bio.getvalue()

    def to_bytes(self) -> bytes:
        return self._to_bytes()

    def to_base64(self) -> str:
        return base64.b64encode(self.to_bytes()).decode('utf-8')

    def to_html(self):
        caption = self.caption or ''
        return f'<img src="data:image/png;base64,{self.to_base64()}" alt="{caption}" style="display:block">'

    def to_widget(self) -> ipywidgets.Widget:
        return ipywidgets.Image(value=self.to_bytes())

    def resize(self, width_or_bbox: int, height: int|None = None) -> 'ImageWrap':
        if height is None:
            new_image = self.image.copy()
            new_image.thumbnail((width_or_bbox, width_or_bbox), Image.LANCZOS)
        else:
            new_image = self.image.resize((width_or_bbox, height), Image.LANCZOS)
        return self.replace_image(new_image)
