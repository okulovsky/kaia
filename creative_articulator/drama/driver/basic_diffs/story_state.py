from dataclasses import dataclass
from ...data import Node

@dataclass
class StoryState:
    current_node: Node|None = None
    finalized: bool = False
