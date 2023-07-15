from typing import *
from kaia.bro.core import ISpace, Slot, RangeInput, BoolInput

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Space(ISpace):
    timestamp: Slot[datetime] = Slot()
    sensor_data: Slot[Any] = Slot(shown=False)
    humidity: Slot[float] = Slot()
    humidifier_request: Slot[Optional[bool]] = Slot(input=BoolInput(), shown=False)
    state: Slot[bool] = Slot()

    low_humidity: Slot[float] = Slot(input=RangeInput(30,70,10, float))
    high_humidity: Slot[float] = Slot(input=RangeInput(40,90,10, float))
    max_running_time: Slot[int] = Slot(input=RangeInput(30,300, 30, int), hint="Max. running time in minutes")
    min_cooldown_time: Slot[int] = Slot(input=RangeInput(30,300,30,int), hint="Min. cooldown time in minutes")

    state_request: Slot[Optional[bool]] = Slot(shown=False)
    state_request_reason: Slot[Optional[str]] = Slot(shown=False)

    def get_name(self):
        return 'dehumidifier'

