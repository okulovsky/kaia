from ...core import *
from .ints import OrdinalDub, CardinalDub
from .plural_agreement import PluralAgreement
from .date_dub import DateDub
from .timedelta_dub import TimedeltaDub

def get_predefined_dubs():
    return [
        CardinalDub(-1000, 1000),
        OrdinalDub(0, 1000),
        TimedeltaDub()
    ]
