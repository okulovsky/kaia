from dataclasses import dataclass
from .image_setup import ImageSetup


@dataclass
class ImageRequest:
    setup: ImageSetup
    activity: str
