from dataclasses import dataclass
from typing import Any
from ..core import IDrawable

@dataclass
class DrawerElement:
    drawable: IDrawable
    metadata: Any

