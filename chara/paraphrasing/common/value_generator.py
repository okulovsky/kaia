import random
from datetime import timedelta

from grammatron.dubs import VariableDub
from grammatron.dubs.implementation.int_dub import _IntDub
from grammatron.globalization.timedelta_dub import TimedeltaDub


def generate_values_for_dub(dub, n: int) -> list:
    if isinstance(dub, TimedeltaDub):
        return _generate_timedelta_values(dub, n)
    if isinstance(dub, _IntDub):
        return _generate_int_values(dub, n)
    raise ValueError(f"Unknown dub type: {type(dub).__name__}")


def _generate_int_values(dub: _IntDub, n: int) -> list[int]:
    if dub.min is None or dub.max is None:
        raise ValueError(f"IntDub has no min/max bounds")
    values = list(range(dub.min, dub.max + 1))
    random.shuffle(values)
    return values[:n]


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


def generate_values_for_template(template, n: int) -> list[dict]:
    dispatch = template.dub.dispatch
    tdub = next(iter(dispatch.values()))
    seq = tdub.sequences[0]

    var_dubs = {
        item.name: item.dub
        for item in seq.sequence
        if isinstance(item, VariableDub)
    }

    if not var_dubs:
        return []

    value_lists = {name: generate_values_for_dub(dub, n) for name, dub in var_dubs.items()}
    n_actual = min(len(vals) for vals in value_lists.values())
    return [{name: vals[i] for name, vals in value_lists.items()} for i in range(n_actual)]
