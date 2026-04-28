import random
from datetime import timedelta

from grammatron import VariableDub, TimedeltaDub, OptionsDub
from grammatron.dubs.implementation.int_dub import _IntDub
import numpy as np




def generate_values_for_dub(dub, n: int) -> list:
    if isinstance(dub, TimedeltaDub):
        return _generate_timedelta_values(dub, n)
    if isinstance(dub, _IntDub):
        return _generate_int_values(dub, n)
    if isinstance(dub, OptionsDub):
        return _generate_options_values(dub, n)
    raise ValueError(f"Unknown dub type: {type(dub).__name__}")


def _generate_options_values(dub: OptionsDub, n: int) -> list:
    return [random.choice(list(dub.value_to_strs)) for _ in range(n)]

def _generate_int_values(dub: _IntDub, n: int) -> list[int]:
    if dub.min is None and dub.max is None:
        min_value = 0
        max_value = 10
    elif dub.min is None:
        max_value = dub.max
        min_value = max_value - 10
    elif dub.max is None:
        min_value = dub.min
        max_value = min_value + 10
    else:
        min_value = dub.min
        max_value = dub.max

    values = list(range(min_value, max_value + 1))
    return [random.choice(values) for _ in range(n)]



_TYPICAL_SECONDS = [5, 10, 15, 20, 30, 45]
_TYPICAL_MINUTES = [1, 2, 3, 5, 10, 15, 20, 30, 45]
_TYPICAL_HOURS = [1, 2, 3, 5, 8, 12, 24]


def _generate_timedelta_values(dub: TimedeltaDub, n: int) -> list[timedelta]:
    # dub.adds = [add_seconds, add_minutes, add_hours]
    add_seconds, add_minutes, add_hours = dub.adds

    values = []
    for _ in range(n):
        kwargs = {}
        if add_hours:
            kwargs['hours'] = random.choice(_TYPICAL_HOURS)
        if add_minutes:
            kwargs['minutes'] = random.choice(_TYPICAL_MINUTES)
        if add_seconds:
            kwargs['seconds'] = random.choice(_TYPICAL_SECONDS)
        if not kwargs:
            kwargs['minutes'] = random.choice(_TYPICAL_MINUTES)
        values.append(timedelta(**kwargs))
    return values


def generate_values_for_variables(variables: list[VariableDub], n: int) -> list[dict]:
    var_dubs = {
        item.name: item.dub
        for item in variables
    }

    if not var_dubs:
        return []

    value_lists = {name: generate_values_for_dub(dub, n) for name, dub in var_dubs.items()}
    n_actual = min(len(vals) for vals in value_lists.values())
    return [{name: vals[i] for name, vals in value_lists.items()} for i in range(n_actual)]
