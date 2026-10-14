import random
import re
from datetime import timedelta
from grammatron import CardinalDub, OrdinalDub, DubParameters, TimedeltaDub
from grammatron.dubs.implementation.categorical_variable_dub import string_values_to_values
from avatar.daemon.stt_service.stt.nlu_slots import slots_to_text, timedelta_to_text, no_command_text

# TextDatasetPipeline stores durations and ordinals as English words, whatever the language of the text
_CARDINALS = string_values_to_values(CardinalDub(0, 120), DubParameters())
_ORDINALS = string_values_to_values(OrdinalDub(1, 10), DubParameters())
_UNITS = {'hour': 'hours', 'hours': 'hours', 'minute': 'minutes', 'minutes': 'minutes', 'second': 'seconds', 'seconds': 'seconds'}

# Closed lists of options: the model outputs the English value Kaia's template has, whatever the language.
# Dataset values that are not in the list (weekdays, weeks, "in three days") are dropped:
# learning them would teach the model to output values Kaia cannot use.
_CLOSED_OPTIONS = {
    'delta': {
        'Today': ['Today', 'This morning', 'This afternoon', 'This evening',
                  'Heute', 'Сегодня', 'Сегодня вечером'],
        'Tomorrow': ['Tomorrow', 'Next day', 'The following day', 'The next morning', 'The next afternoon',
                     'The following night', 'The subsequent day', 'The ensuing day', 'The upcoming day',
                     'The coming day', 'The forthcoming day',
                     'Morgen', 'Morgen früh', 'Am Tag danach', 'Завтра', 'Завтра утром'],
        'Yesterday': ['Yesterday', 'Previous day', 'The preceding day', 'The previous evening', 'The previous morning',
                      'The preceding morning', 'The past day', 'The prior day', 'The former day', 'The earlier day',
                      'Last night', 'Gestern', 'Gestern Abend', 'Am Tag davor', 'Вчера', 'Вчера вечером'],
        'The day after tomorrow': ['The day after tomorrow', 'Day after next', 'In two days', 'Two days from now',
                                   'Übermorgen', 'Übermorgen Nachmittag', 'In zwei Tagen',
                                   'Послезавтра', 'Послезавтра ночью'],
        'The day before yesterday': ['The day before yesterday', 'Vorgestern', 'Vorgestern Nacht',
                                     'Позавчера', 'Позавчера днем'],
    }
}
_CLOSED_OPTIONS_INDEX = {
    name: {said.lower(): value for value, saids in options.items() for said in saids}
    for name, options in _CLOSED_OPTIONS.items()
}


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
        name, value = variable['name'], variable['value']
        if variable['type'] == 'TimedeltaDub':
            duration = _parse_duration(value)
            if duration is None:
                return None
            slots[name] = timedelta_to_text(duration)
        elif variable['type'] == 'OrdinalDub':
            if value.lower() not in _ORDINALS:
                return None
            slots[name] = str(_ORDINALS[value.lower()])
        elif name in _CLOSED_OPTIONS_INDEX:
            if value.lower() not in _CLOSED_OPTIONS_INDEX[name]:
                return None
            slots[name] = _CLOSED_OPTIONS_INDEX[name][value.lower()]
        else:
            slots[name] = value
    return slots


def record_to_sample(record: dict) -> dict | None:
    slots = record_to_slots(record)
    if slots is None:
        return None
    return dict(INPUT=record['text'], OUTPUT=slots_to_text(slots, record['intent']))


def negative_to_sample(text: str) -> dict:
    """A phrase that is not a command: the model must answer `intent: none`"""
    return dict(INPUT=text, OUTPUT=no_command_text())


_TIMER_PHRASES = {
    'en': ['Set the timer for {}', 'Set a timer for {}', 'Timer for {}', 'Can you set a timer for {}?', 'Start a timer for {}'],
    'de': ['Stell einen Timer auf {}', 'Stelle den Timer auf {}', 'Timer auf {}', 'Kannst du einen Timer für {} stellen?'],
    'ru': ['Поставь таймер на {}', 'Установи таймер на {}', 'Таймер на {}', 'Засеки {}', 'Можешь поставить таймер на {}?'],
}

# Russian timer phrases need the accusative: "на одну минуту", not "на одна минута"
_RU_ACCUSATIVE = [('одна ', 'одну '), ('минута', 'минуту'), ('секунда', 'секунду')]


def synthetic_timer_records(intent: str, per_language: int = 60, seed: int = 0) -> list[dict]:
    """
    Short timers: TextDatasetPipeline generated mostly "hours and minutes", so the model confused
    "five minutes" or "thirty seconds". The phrases are rendered by grammatron's TimedeltaDub.
    """
    rnd = random.Random(seed)
    dub = TimedeltaDub()
    records = []
    for language, phrases in _TIMER_PHRASES.items():
        for i in range(per_language):
            kind = i % 4
            if kind == 0:
                duration = timedelta(minutes=rnd.randint(1, 59))
            elif kind == 1:
                duration = timedelta(seconds=rnd.choice([5, 10, 15, 20, 30, 40, 45, 50]))
            elif kind == 2:
                duration = timedelta(hours=rnd.randint(1, 12))
            else:
                duration = timedelta(minutes=rnd.randint(1, 59), seconds=rnd.choice([10, 15, 20, 30, 45]))
            said = dub.to_str(duration, DubParameters(language=language))
            if language == 'ru':
                for old, new in _RU_ACCUSATIVE:
                    said = said.replace(old, new)
            records.append(dict(
                text=rnd.choice(phrases).format(said),
                intent=intent,
                language=language,
                values=[dict(name='duration', type='TimedeltaDub', value=dub.to_str(duration, DubParameters()))],
            ))
    return records
