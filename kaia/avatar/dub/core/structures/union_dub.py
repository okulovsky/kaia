from typing import *
from .dub import Dub
from .sequence_dub import SequenceDub
from .dub_binding import DubBinding
import re
import numpy as np

class UnionDub(Dub):
    def __init__(self,
                 sequences: Iterable[SequenceDub],
                 value_to_dict: Optional[Callable[[Any], Dict]] = None,
                 dict_to_value: Optional[Callable[[Dict], Any]] = None,
                 strict_dict_equality_in_to_str=True
                 ):
        self._sequences = tuple(sequences)
        self._value_to_dict = value_to_dict
        self._dict_to_value = dict_to_value
        self._strict_dict_equality_in_to_str = strict_dict_equality_in_to_str
        self._name = '/'.join(c.get_name() for c in self._sequences)

    @property
    def sequences(self):
        return self._sequences

    @property
    def value_to_dict(self):
        return self._value_to_dict

    @property
    def dict_to_value(self):
        return self._dict_to_value

    @property
    def strict_dict_equality_in_to_str(self):
        return self._strict_dict_equality_in_to_str

    def get_name(self):
        return self._name

    @staticmethod
    def create_sequences(
            strings: Iterable[str],
            dubs: Dict[str, Union[Dub, DubBinding]],
            sequence_prefix: str = 'Sequence'
    ) -> List[SequenceDub]:
        result = []
        for s in strings:
            parts = re.split('({[a-z0-9_]+})', s)
            arguments = []
            for part in parts:
                if len(part) == 0:
                    continue
                if part[0] == '{':
                    key = part.replace('{', '').replace('}', '')
                    if key not in dubs:
                        raise ValueError(
                            f"The string contains key {key} that is not in the variables list {' '.join(dubs)}. The string\n{s}")
                    if isinstance(dubs[key], Dub):
                        arguments.append(DubBinding.variable(dubs[key], key))
                    elif isinstance(dubs[key], DubBinding):
                        arguments.append(dubs[key])
                    else:
                        raise ValueError(f'Key {key} expects to contain Dub or DubBinging, but was {type(dubs[key])}')
                else:
                    arguments.append(DubBinding.constant(part))
            result.append(SequenceDub(arguments, f'[{sequence_prefix}]: {s}'))
        return result

