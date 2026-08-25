from dataclasses import dataclass
from ...data import Node
from ..plan import Plan
from ...scene import SceneHint


@dataclass
class ElaborationCase:
    node: Node
    plan: Plan
    hint_json_example: str
    stages: SceneHint|None = None




