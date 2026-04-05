from dataclasses import dataclass
from ....framework import ConnectionSettings


@dataclass
class VideoToImagesSettings:
    connection = ConnectionSettings(20305, 120)