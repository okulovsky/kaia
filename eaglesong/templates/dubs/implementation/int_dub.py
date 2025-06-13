from typing import Any
from ..core import CategoricalVariableDub, DubParameters
import num2words

_SUFFIXES = {1: 'st', 2:'nd', 3:'rd'}

class _IntDub(CategoricalVariableDub):
    def __init__(self, is_ordinal: bool, min:int|None = None, max:int|None=None):
        self.is_ordinal = is_ordinal
        self.min = min
        self.max = max

    def get_values(self):
        if self.min is None or self.max is None:
            raise ValueError("min or max aren't defined, cannot use for parsing")
        return range(self.min, self.max+1)

    def value_to_all_strs(self, value, parameters: DubParameters, first_only: bool):
        if self.is_ordinal:
            rem = _SUFFIXES.get(value%10,'th')
            as_num = f'{value}{rem}'
        else:
            as_num = str(value)

        s = num2words.num2words(value, self.is_ordinal, lang=parameters.language)

        if parameters.spoken:
            yield s
            yield as_num
        else:
            yield as_num
            yield s



class CardinalDub(_IntDub):
    def __init__(self, min: int|None = None, max: int|None = None):
        if min is not None and max is None:
            max = min
            min = 0
        super().__init__(False, min, max)


class OrdinalDub(_IntDub):
    def __init__(self, min: int | None = None, max: int | None = None):
        if min is not None and max is None:
            max = min
            min = 0
        super().__init__(True, min, max)



