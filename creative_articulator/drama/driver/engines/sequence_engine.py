from typing import Iterable

from .engine import IEngine, EngineOutput
from ...data import Node
from ..basic_diffs import PushDiff, PopDiff

class SequenceEngine(IEngine):
    def generate(self, current: Node) -> Iterable[EngineOutput]:
        child = PushDiff.find_non_finalized_child(current)
        if child is None:
            yield PopDiff()
        else:
            yield PushDiff()
