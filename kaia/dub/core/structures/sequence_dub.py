from typing import *
from .dub import Dub
from .constant_dub import ConstantDub
from .dub_binding import IDubBinding

class SequenceDub(Dub):
    def __init__(self,
                 steps: Iterable[IDubBinding],
                 sequence_name: Optional[str] = None
                 ):
        self._steps = tuple(steps)
        all_keys = []
        for step in self._steps:
            consumed_keys = step.get_consumed_keys()
            if consumed_keys is None:
                raise ValueError(step)
            for key in consumed_keys:
                all_keys.append(key)
        self._consumed_keys = tuple(sorted(set(all_keys)))
        sequence_name_parts = [step.type.value if isinstance(step.type, ConstantDub) else f'{{{step.name}}}' for step in self._steps]
        if sequence_name is None:
            self._sequence_name = '[Sequence]: '+' '.join(sequence_name_parts)
        else:
            self._sequence_name = sequence_name

    @property
    def steps(self):
        return self._steps

    @property
    def consumed_keys(self):
        return self._consumed_keys

    def get_name(self):
        return self._sequence_name

