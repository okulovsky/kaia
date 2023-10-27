from ...core import DubBinding, DictDub
from functools import partial

def _plural_detector(d, name):
    if name not in d:
        raise ValueError(f"Key {name} is absent")
    value = d[name]
    if not isinstance(value, int):
        raise ValueError(f'By key {name} expected int, but was {d[name]} of type {type(d[name])}')
    return value==1 or value==-1


class PluralAgreement(DubBinding):
    def __init__(self, field_to_agree_on, singular_form, plural_form = None):
        if plural_form is None:
            plural_form = singular_form+'s'
        super().__init__(
            DictDub({True: singular_form, False: plural_form}),
            field_to_agree_on,
            False,
            True,
            partial(_plural_detector, name = field_to_agree_on)
        )
