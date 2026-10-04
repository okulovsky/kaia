"""
The text format of the slots model (the LoRA adapter of NluRecognitionSetup) and its conversion to template values.

The model receives the recognized text and outputs one `name: value` line per variable, after a line break:
durations as `H:MM:SS`, numbers as digits, options as they were said. `-` means that no variable was said.
"""
from datetime import timedelta
from typing import Any
from grammatron import (
    Template, LanguageDispatchDub, VariableDub, DubParameters, TimedeltaDub, CategoricalVariableDub,
)
from grammatron.dubs.implementation.int_dub import _IntDub

EMPTY = '-'


def slots_to_text(slots: dict[str, str]) -> str:
    if len(slots) == 0:
        return '\n' + EMPTY
    return '\n' + '\n'.join(f'{name}: {value}' for name, value in slots.items())


def text_to_slots(text: str) -> dict[str, str] | None:
    """Returns None if the text is not in the format of the slots model."""
    slots = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if line == '' or line == EMPTY:
            continue
        name, separator, value = line.partition(':')
        if separator == '' or name.strip() == '' or value.strip() == '':
            return None
        slots[name.strip()] = value.strip()
    return slots


def timedelta_to_text(value: timedelta) -> str:
    seconds = int(value.total_seconds())
    return f'{seconds // 3600}:{seconds // 60 % 60:02d}:{seconds % 60:02d}'


def template_variables(template: Template) -> dict[str, VariableDub]:
    dub = template.dub
    dubs = dub.dispatch.values() if isinstance(dub, LanguageDispatchDub) else [dub]
    variables = {}
    for d in dubs:
        for sequence in getattr(d, 'sequences', None) or []:
            for leaf in sequence.get_leaves():
                if isinstance(leaf, VariableDub):
                    variables.setdefault(leaf.name, leaf)
    return variables


def slots_to_values(template: Template, slots: dict[str, str]) -> dict[str, Any] | None:
    """Converts the model's slots to the values of the template; None if any of them does not fit."""
    variables = template_variables(template)
    values = {}
    for name, text in slots.items():
        if name not in variables:
            return None
        value = _parse_value(variables[name].dub, text)
        if value is None:
            return None
        values[name] = value
    return values


def _parse_value(dub, text: str):
    if isinstance(dub, TimedeltaDub):
        parts = text.split(':')
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            return None
        value = timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))
        return value if value.total_seconds() > 0 else None
    if isinstance(dub, _IntDub):
        if not text.isdigit():
            return None
        value = int(text)
        if dub.min is not None and dub.max is not None and not dub.min <= value <= dub.max:
            return None
        return value
    if isinstance(dub, CategoricalVariableDub):
        wanted = text.lower()
        for value in dub.get_values():
            if any(s.lower() == wanted for s in dub.value_to_all_strs(value, DubParameters())):
                return value
        return None
    return None
