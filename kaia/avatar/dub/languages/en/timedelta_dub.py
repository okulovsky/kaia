from typing import *
from ...core import UnionDub, IRandomizableDub
from .int_dub import CardinalDub
from .plural_agreement import PluralAgreement
from datetime import timedelta, time
import numpy as np

_strings = [
    '{seconds} {seconds_word}',
    '{minutes} {minutes_word} and {seconds} {seconds_word}',
    '{hours} {hours_word}, {minutes} {minutes_word} and {seconds} {seconds_word}',
    '{days} {days_word}, {hours} {hours_word}, {minutes} {minutes_word} and {seconds} {seconds_word}',
]




def create_dubs():
    result = {}
    for key in ['days','hours','minutes','seconds']:
        result[key] = CardinalDub(0, 1000)
        result[key+'_word'] = PluralAgreement(key, key[:-1], key)
    return result


class TimedeltaDub(UnionDub, IRandomizableDub):
    def __init__(self):
        super().__init__(
            UnionDub.create_sequences(
                _strings,
                create_dubs(),
                'TimedeltaDub'
            ),
            value_to_dict = TimedeltaDub.timedelta_to_dict,
            dict_to_value = TimedeltaDub.dict_to_timedelta
        )

    def get_random_value(self, random_state: Optional[np.random.RandomState] = np.random.RandomState()):
        return timedelta(seconds=random_state.randint(0,10000))


    def get_name(self):
        return 'TimedeltaDub'

    @staticmethod
    def timedelta_to_dict(duration: timedelta):
        days, seconds = duration.days, duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        result = dict(seconds=seconds)

        if days != 0:
            result['days'] = days
            result['hours'] = hours
            result['minutes'] = minutes
        elif hours!=0:
            result['hours'] = hours
            result['minutes'] = minutes
        elif minutes!=0:
            result['minutes'] = minutes
        return result

    @staticmethod
    def dict_to_timedelta(d):
        seconds = d.get('seconds', 0)
        seconds += d.get('minutes', 0)*60
        seconds += d.get('hours', 0)*3600
        days = d.get('days', 0)
        return timedelta(days, seconds)


