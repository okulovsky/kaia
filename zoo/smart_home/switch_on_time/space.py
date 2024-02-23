from typing import *
from kaia.bro.core import ISpace, Slot, RangeInput, SetInput

from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Space(ISpace):
    name: str
    timestamp: Slot[datetime] = Slot.field()
    sensor_data: Slot[Any] = Slot.field(stored=False, shown=False)
    switch_state: Slot[bool] = Slot.field()
    switch_request: Slot[Optional[bool]] = Slot.field()

    def get_name(self):
        return self.name

