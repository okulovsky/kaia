from dataclasses import dataclass
from chara.common import ICase
from .image_setup import ImageSetup


@dataclass
class ImageRequest(ICase):
    setup: ImageSetup
    activity: str
