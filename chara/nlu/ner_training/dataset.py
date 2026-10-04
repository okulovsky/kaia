import re
from datetime import timedelta
from grammatron import CardinalDub, OrdinalDub, DubParameters
from grammatron.dubs.implementation.categorical_variable_dub import string_values_to_values
from avatar.daemon.stt_service.stt.nlu_slots import slots_to_text, timedelta_to_text

# TextDatasetPipeline stores durations and ordinals as English words, whatever the language of the text
_CARDINALS = string_values_to_values(CardinalDub(0, 120), DubParameters())
_ORDINALS = string_values_to_values(OrdinalDub(1, 10), DubParameters())
_UNITS = {'hour': 'hours', 'hours': 'hours', 'minute': 'minutes', 'minutes': 'minutes', 'second': 'seconds', 'seconds': 'seconds'}


def _parse_duration(text: str) -> timedelta | None:
    parts = {}
    for chunk in re.split(r',\s*|\s+and\s+', text.strip().lower()):
        words = chunk.split()
        if len(words) < 2 or words[-1] not in _UNITS:
            return None
        number = ' '.join(words[:-1])
        if number not in _CARDINALS:
            return None
        parts[_UNITS[words[-1]]] = _CARDINALS[number]
    return timedelta(**parts) if parts else None


def record_to_slots(record: dict) -> dict[str, str] | None:
    """The target slots of a text-dataset record, None if a value cannot be read."""
    slots = {}
    for variable in record['values']:
        value = variable['value']
        if variable['type'] == 'TimedeltaDub':
            duration = _parse_duration(value)
            if duration is None:
                return None
            slots[variable['name']] = timedelta_to_text(duration)
        elif variable['type'] == 'OrdinalDub':
            if value.lower() not in _ORDINALS:
                return None
            slots[variable['name']] = str(_ORDINALS[value.lower()])
        else:
            slots[variable['name']] = value
    return slots


def record_to_sample(record: dict) -> dict | None:
    slots = record_to_slots(record)
    if slots is None:
        return None
    return dict(INPUT=record['text'], OUTPUT=slots_to_text(slots))
