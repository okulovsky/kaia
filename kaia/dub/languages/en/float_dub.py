from typing import *
import numpy as np
from ...core import UnionDub, IRandomizableDub, DictDub
from .int_dub import CardinalDub

special_parts = {
    2 : 'half',
    3 : 'third',
    4 : 'quarter'
}

zeros = {
    1: 'zero',
    2: 'zero zero',
    3: 'zero zero zero',
    4: 'zero zero zero zero'
}


class FloatDub(UnionDub, IRandomizableDub):
    def __init__(self, max_value: int = 1000, precision: int =2):
        self.precision = precision
        self.max_value = max_value
        super().__init__(
            UnionDub.create_sequences(
                [
                    '{int_value}',
                    '{int_value} point {fraction}',
                    '{int_value} point {zero_count} {fraction}',
                    '{int_value} and a {special_fraction}'
                ],
                dict(
                    int_value = CardinalDub(0, max_value),
                    fraction = CardinalDub(0,10**precision),
                    special_fraction = DictDub(special_parts),
                    zero_count = DictDub(zeros)
                )
            ),
            self._value_to_dict,
            self._dict_to_value
        )

    def _value_to_dict(self, value):
        int_part = int(value)
        fraction = round(value - int_part, self.precision)
        special = None
        if fraction == 0.5:
            special=2
        elif str(fraction) == '0.'+'3'*self.precision:
            special=3
        elif fraction == 0.25:
            special=4
        if special is not None:
            return dict(int_value = int_part, special_fraction=special)
        fraction = str(fraction)[2:]
        zero_count = 0
        while fraction.startswith('0'):
            fraction = fraction[1:]
            zero_count+=1
        if fraction == '':
            return dict(int_value = int_part)
        elif zero_count == 0:
            return dict(int_value = int_part, fraction = fraction)
        else:
            return dict(int_value = int_part, fraction = fraction, zero_count = zero_count)

    def _dict_to_value(self, d):
        if 'special_fraction' in d:
            return d['int_value'] + round(1/d['special_fraction'], self.precision)
        elif 'fraction' in d:
            fraction = d['fraction'] / (10**(len(str(d['fraction'])) + d.get('zero_count', 0)))
            return d['int_value'] + fraction
        else:
            return d['int_value']

    def get_random_value(self, random_state: Optional[np.random.RandomState] = np.random.RandomState()):
        value = int(random_state.random()*(self.max_value*10**self.precision))/(10**self.precision)
        return value
