from typing import *
from ...core import UnionDub, IRandomizableDub
from .int_dub import CardinalDub
from .plural_agreement import PluralAgreement
from datetime import timedelta, time
import numpy as np



def create_template(max_days, max_hours):
    templates = []
    dubs = {}

    templates.append('{seconds} {seconds_word}')
    dubs['seconds'] = CardinalDub(0, 60)

    templates.append('{minutes} {minutes_word} and {seconds} {seconds_word}')
    dubs['minutes'] = CardinalDub(0,60)

    if max_hours>0:
        templates.append('{hours} {hours_word}, {minutes} {minutes_word} and {seconds} {seconds_word}')
        dubs['hours'] = CardinalDub(0, max_hours)

    if max_days > 0:
        templates.append('{days} {days_word}, {hours} {hours_word}, {minutes} {minutes_word} and {seconds} {seconds_word}')
        dubs['days'] = CardinalDub(0, max_days)

    for key in list(dubs):
        dubs[key + '_word'] = PluralAgreement(key, key[:-1], key)

    return templates, dubs


class TimedeltaDub(UnionDub, IRandomizableDub):
    def __init__(self, max_days=1000, max_hours=1000):
        templates, dubs = create_template(max_days, max_hours)
        super().__init__(
            UnionDub.create_sequences(
                templates,
                dubs,
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


