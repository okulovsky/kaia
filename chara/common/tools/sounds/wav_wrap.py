import ipywidgets

from ..core import IDrawable
from dataclasses import dataclass
import base64
from pathlib import Path
from yo_fluq import FileIO
from .wav_editable import WavEditable


@dataclass
class WavWrap(IDrawable):
    name: str | None
    content: bytes | None
    path: Path | None

    def __post_init__(self):
        if self.content is None and self.path is None:
            raise ValueError("Neither content nor path was initialized")

    def to_base64(self) -> str:
        return base64.b64encode(self.to_bytes()).decode('utf-8')

    def to_widget(self) -> ipywidgets.Widget:
        return ipywidgets.Audio(value=self.to_bytes(), autoplay=False)

    def to_html(self):
        b64 = self.to_base64()
        return f"""
    <figure>
      <figcaption>{self.name}</figcaption>
      <audio controls>
        <source src="data:audio/wav;base64,{b64}" type="audio/wav">
        Your browser does not support the audio element.
      </audio>
    </figure>
    """.strip()

    def to_bytes(self) -> bytes:
        if self.content is None:
            self.content = FileIO.read_bytes(self.path)
        return self.content

    def to_editable(self) -> WavEditable:
        bts = self.content
        if bts is None:
            bts = FileIO.read_bytes(self.path)
        return WavEditable.from_bytes(bts)


