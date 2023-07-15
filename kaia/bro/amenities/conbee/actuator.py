from typing import *
from ...core import ISpace, Slot
from .driver import Driver

class SwitchActuator:
    def __init__(self, slot: Union[str, Slot], switch_key):
        self.slot_name = Slot.slotname(slot)
        self.switch_key = switch_key

    def __call__(self, space: ISpace):
        slot = space.get_slot(self.slot_name)
        if slot.current_value is not None:
            Driver.get_current().execute_switch_command(self.switch_key, slot.current_value)

