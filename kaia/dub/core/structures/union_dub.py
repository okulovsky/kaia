from typing import *
from .dub import Dub
from .sequence_dub import SequenceDub
from .dub_binding import IDubBinding
import re
import numpy as np

class UnionDub(Dub):
    def __init__(self,
                 sequences: Iterable[SequenceDub],
                 value_to_dict: Optional[Callable[[Any], Dict]] = None,
                 dict_to_value: Optional[Callable[[Dict], Any]] = None,
                 strict_dict_equality_in_to_str=True,
                 treat_none_as_missing_value=True
                 ):
        self._sequences = tuple(sequences)
        self._value_to_dict = value_to_dict
        self._dict_to_value = dict_to_value
        self._strict_dict_equality_in_to_str = strict_dict_equality_in_to_str
        self._treat_none_as_missing_value=treat_none_as_missing_value
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

    @property
    def treat_none_as_missing_value(self):
        return self._treat_none_as_missing_value

    def get_name(self):
        return self._name



    @staticmethod
    def create_sequences(
            strings: Iterable[str],
            dubs: Dict[str, Union[Dub, IDubBinding]],
            sequence_prefix: str = 'Sequence',
            auto_create_dub_factory: Optional[Callable] = None
    ) -> List[SequenceDub]:
        result = []
        for s in strings:
            parts = re.split('({[A-Za-z0-9_]+})', s)
            arguments = []
            for part in parts:
                if len(part) == 0:
                    continue
                if part[0] == '{':
                    key = part.replace('{', '').replace('}', '')
                    if key not in dubs:
                        if auto_create_dub_factory is None:
                            raise ValueError(f"The string contains key {key} that is not in the variables list {' '.join(dubs)}. The string\n{s}")
                        else:
                            dubs[key] = auto_create_dub_factory()
                    if isinstance(dubs[key], Dub):
                        arguments.append(IDubBinding.variable(dubs[key], key))
                    elif isinstance(dubs[key], IDubBinding):
                        dubs[key].set_name(key)
                        arguments.append(dubs[key])
                    else:
                        raise ValueError(f'Key {key} expects to contain Dub or DubBinging, but was {type(dubs[key])}')
                else:
                    arguments.append(IDubBinding.constant(part))
            result.append(SequenceDub(arguments, f'[{sequence_prefix}]: {s}'))
        return result

