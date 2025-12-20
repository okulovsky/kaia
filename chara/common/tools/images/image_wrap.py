import ipywidgets
from PIL import Image
from dataclasses import dataclass
import io
import base64
from ..core import IDrawable

@dataclass
class ImageWrap(IDrawable):
    image: Image.Image
    caption: str | None = None

    def replace_image(self, new_image: Image.Image):
        return ImageWrap(image=new_image, caption=self.caption)

    def _to_bytes(self) -> bytes:
        bio = io.BytesIO()
        self.image.save(bio, 'PNG')
        return bio.getvalue()

    def to_bytes(self) -> bytes:
        return self._to_bytes()

    def to_base64(self) -> str:
        return base64.b64encode(self.to_bytes()).decode('utf-8')

    def to_html(self):
        return f'<img src="data:image/png;base64, {self.to_base64()}" alt="{self.caption}">'

    def to_widget(self) -> ipywidgets.Widget:
        return ipywidgets.Image(value=self.to_bytes())