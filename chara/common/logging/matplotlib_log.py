from matplotlib.figure import Figure
from .log_item import ILogItem
from dataclasses import dataclass
from .image_log import ImageLogItem
import io

@dataclass
class FigureLogItem(ILogItem):
    figure: Figure

    def to_string(self) -> str:
        return '[Plot]'

    def to_html(self) -> str:
        buf = io.BytesIO()
        self.figure.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        bytes = buf.read()
        return ImageLogItem.bytes_to_img_tag(bytes)