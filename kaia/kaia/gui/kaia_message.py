from dataclasses import dataclass
from typing import *
@dataclass
class KaiaMessage:
    is_bot: bool
    text: str
    is_error: bool = False
    speaker: Optional[str] = None
    avatar: Optional[str] = None