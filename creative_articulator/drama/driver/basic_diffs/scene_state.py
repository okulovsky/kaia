from ...data import Message
from dataclasses import dataclass, field

@dataclass
class SceneState:
    messages: list[Message] = field(default_factory=list)
    finalized: bool = False

    summary: str|None = None
    shortening: str|None = None
    shortening_index: int = 0

