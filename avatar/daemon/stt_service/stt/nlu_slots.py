"""
The text format of the slots model (the LoRA adapter of NluRecognitionSetup) and its conversion to template values.

The model receives the recognized text and outputs, after a line break, the intent and then one `name: value`
line per variable:

    intent: TimerIntents.set_the_timer
    duration: 1h 30m

The intent is `TemplatesCollection.template`, or `none` if the text is not a command. Durations are `1h 30m`
(only non-zero parts), numbers are digits, options are as they were said, closed lists of options
(e.g. the relative day) are their English value. Adapters trained before the intent line output only the variables,
with `-` for no variables; they are still read.
"""
import re
from datetime import timedelta
from typing import Any
from grammatron import (
    Template, LanguageDispatchDub, VariableDub, DubParameters, TimedeltaDub, CategoricalVariableDub,
)
from grammatron.dubs.implementation.int_dub import _IntDub

EMPTY = '-'
INTENT = 'intent'
NO_INTENT = 'none'


def intent_label(intent: str | None) -> str:
    """`kaia.skills.timer_skill.TimerIntents.set_the_timer` -> `TimerIntents.set_the_timer`"""
    if intent is None:
        return NO_INTENT
    return '.'.join(intent.split('.')[-2:])


def slots_to_text(slots: dict[str, str], intent: str | None = None) -> str:
    """The model's output. With `intent`, the output starts with the intent line (pass a full intent name)."""
    lines = [] if intent is None else [f'{INTENT}: {intent_label(intent)}']
    lines += [f'{name}: {value}' for name, value in slots.items()]
    if len(lines) == 0:
        return '\n' + EMPTY
    return '\n' + '\n'.join(lines)


def no_command_text() -> str:
    """The model's output for a text that is not a command"""
    return f'\n{INTENT}: {NO_INTENT}'


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


_DURATION = re.compile(r'^(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?$')


def timedelta_to_text(value: timedelta) -> str:
    seconds = int(value.total_seconds())
    parts = [(seconds // 3600, 'h'), (seconds // 60 % 60, 'm'), (seconds % 60, 's')]
    return ' '.join(f'{n}{unit}' for n, unit in parts if n > 0)


def text_to_timedelta(text: str) -> timedelta | None:
    match = _DURATION.match(text.strip())
    if match is None:
        return None
    hours, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    value = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return value if value.total_seconds() > 0 else None


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
        return text_to_timedelta(text)
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
