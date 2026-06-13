from dataclasses import dataclass
from ...common import IImageScenario
from brainbox.deciders.images.comfyui.workflows import TextToImage
from pathlib import Path
from typing import Any
from chara import ICase

@dataclass
class DrawingCase(ICase):
    scenario: IImageScenario
    workflow: TextToImage|None = None
    image: Path|None = None
    face_detection: Any = None
    self_review: Any = None

