from typing import *
from kaia.bro.core import ISpace, Slot, RangeInput, BoolInput

from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Space(ISpace):
    timestamp: Slot[datetime] = Slot()
    sensor_data: Slot[Any] = Slot(shown=False)
    temperature_on_thermostat: Slot[float] = Slot()
    temperature_on_sensor: Slot[float] = Slot()
    temperature_setpoint: Slot[float] = Slot()
    valve_position: Slot[float] = Slot()

    def get_name(self):
        return 'heating'