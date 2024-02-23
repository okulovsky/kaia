from typing import *
from kaia.bro.core import ISpace, Slot, RangeInput, SetInput

from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Space(ISpace):
    name: str
    timestamp: Slot[datetime] = Slot.field()
    sensor_data: Slot[Any] = Slot.field(shown=False)
    temperature_on_thermostat: Slot[float] = Slot.field()
    temperature_on_sensor: Slot[float] = Slot.field()
    temperature_setpoint: Slot[float] = Slot.field()
    valve_position: Slot[float] = Slot.field()
    update_time: Slot[float] = Slot.field()

    temperature_setpoint_request: Slot[Optional[float]] = Slot.field(input=RangeInput(15,23, 0.5).value_from('temperature_setpoint'), hint="Request temperature")
    temperature_setpoint_command: Slot[Optional[int]] = Slot.field(shown=False)
    temperature_setpoint_feedback: Slot[Optional[str]] = Slot.field(shown=False)

    plan: Slot[Optional[str]] = Slot.field()
    plan_request: Slot[Optional[str]] = Slot.field(input = SetInput([]).value_from('plan'), hint='Request plan')
    plan_delta: Slot[Optional[float]] = Slot.field(input = RangeInput(-3,3, 0.5), hint = 'Delta to plan value')



    def get_name(self):
        return self.name

