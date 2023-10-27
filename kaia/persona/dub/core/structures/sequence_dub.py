from typing import *
from .dub import Dub
from .constant_dub import ConstantDub
from .dub_binding import DubBinding
from yo_fluq_ds import Query
import numpy as np

class SequenceDub(Dub):
    def __init__(self,
                 steps: Iterable[DubBinding],
                 sequence_name: Optional[str] = None
                 ):
        self._steps = tuple(steps)
        self._produced_keys = tuple(sorted(set(step.name for step in self._steps if step.produces_value)))
        self._consumed_keys = tuple(sorted(set(step.name for step in self._steps if step.consumes_value)))
        sequence_name_parts = [step.type.value if isinstance(step.type, ConstantDub) else f'{{{step.name}}}' for step in self._steps]
        if sequence_name is None:
            self._sequence_name = '[Sequence]: '+' '.join(sequence_name_parts)
        else:
            self._sequence_name = sequence_name

    @property
    def steps(self):
        return self._steps

    @property
    def produced_keys(self):
        return self._produced_keys

    @property
    def consumed_keys(self):
        return self._consumed_keys

    def get_name(self):
        return self._sequence_name

