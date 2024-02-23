from typing import *
from ..core import ISpace, Slot
from ...infra.comm import IMessenger
import datetime

class SettingsHandler:
    def __init__(self, slot_name: Union[str, Slot], value: Any):
        if isinstance(slot_name, Slot):
            slot_name = slot_name.name
        self.slot_name = Slot.slotname(slot_name)
        self.value = value

    def __call__(self, space: ISpace):
        slot = space.get_slot(self.slot_name)
        if slot.current_value is None:
            slot.current_value = slot.history.first_or_default(self.value)
            if slot.current_value is None: #In case when it's a new field after deployment, history is null and default is not null
                slot.current_value = self.value


class Incrementer:
    def __init__(self, slot_name: Union[str, Slot], start_value: Any = 0, delta: Any = 1):
        self.slot_name = Slot.slotname(slot_name)
        self.start_value = start_value
        self.delta = delta

    def __call__(self, space: ISpace):
        slot = space.get_slot(self.slot_name)
        if slot.history.take(1).count()==0:
            slot.current_value = self.start_value
        else:
            slot.current_value = slot.last_value+self.delta

class Timer:
    def __init__(self, slot_name: Union[str, Slot], mock_time_delta_in_seconds = None):
        self.slot_name = Slot.slotname(slot_name)
        self.mock_time_delta_in_seconds = mock_time_delta_in_seconds
        self.call_time = datetime.datetime.now()


    def __call__(self, space: ISpace):
        slot = space.get_slot(self.slot_name)
        if self.mock_time_delta_in_seconds is None:
            slot.current_value = datetime.datetime.now()
        else:
            self.call_time+=datetime.timedelta(seconds=self.mock_time_delta_in_seconds)
            slot.current_value = self.call_time


class ValuesInjector:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.counter = 0

    def __call__(self, space: ISpace):
        if self.counter >= len(self.data):
            return
        row = self.data[self.counter]
        for key, value in row.items():
            space.get_slot(key).current_value = value
        self.counter += 1


class ChangeDetector:
    def __init__(self, from_slot: Union[str, Slot], to_slot: Union[str, Slot]):
        self.from_slot = Slot.slotname(from_slot)
        self.to_slot = Slot.slotname(to_slot)

    def __call__(self, space: ISpace):
        from_slot = space.get_slot(self.from_slot)
        old_value = from_slot.last_value
        current_value = from_slot.current_value
        if (
                (old_value is None and current_value is not None) or
                (old_value is not None and current_value is None) or
                (old_value != current_value)
        ):
            space.get_slot(self.to_slot).current_value = current_value

