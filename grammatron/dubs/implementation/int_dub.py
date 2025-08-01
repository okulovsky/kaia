from typing import Any
from ..core import DubParameters
from .categorical_variable_dub import CategoricalVariableDub
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

    def _value_to_numeric_str(self, value, parameters: DubParameters):
        rem = ''
        if self.is_ordinal and parameters.language == 'en':
            rem = _SUFFIXES.get(value % 10, 'th')
        return f'{value}{rem}'

    def _value_to_str(self, value, parameters: DubParameters):
        return num2words.num2words(value, self.is_ordinal, lang=parameters.language)

    def value_to_str(self, value, parameters: DubParameters):
        if not parameters.spoken:
            return self._value_to_numeric_str(value, parameters)
        return parameters.grammar_rule.to_correct_form(self._value_to_str(value, parameters), value, self)

    def value_to_all_strs(self, value, parameters: DubParameters):
        yield self._value_to_numeric_str(value, parameters)
        s = self._value_to_str(value, parameters)
        all_forms = parameters.grammar_rule.all_morphological_forms(s, value, self)
        yield from all_forms



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



