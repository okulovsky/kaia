from typing import *
from ...core import ISpace, Slot
from .driver import Driver
from .parser import ParserRule

#TODO: remove. Use actuator instead
class SwitchActuator:
    def __init__(self, slot: Union[str, Slot], switch_key):
        self.slot_name = Slot.slotname(slot)
        self.switch_key = switch_key

    def __call__(self, space: ISpace):
        slot = space.get_slot(self.slot_name)
        if slot.current_value is not None:
            Driver.get_current().execute_switch_command(self.switch_key, slot.current_value)



class Actuator:
    def __init__(self,
                 sensors_data_slot: Union[str, Slot],
                 section_key: Optional[str],
                 uid: str,
                 property_endpoint: str,
                 property_name: str,
                 value_slot: Union[str, Slot],
                 feedback_slot: Union[str, Slot, None]
                 ):
        self.sensors_data_slot_name = Slot.slotname(sensors_data_slot)
        self.section_key = section_key
        self.uid = uid
        self.property_endpoint = property_endpoint
        self.property_name = property_name
        self.value_slot_name = Slot.slotname(value_slot)
        self.feedback_slot_name = Slot.slotname(feedback_slot)


    def __call__(self, space: ISpace):
        sensors_data = space.get_slot(self.sensors_data_slot_name).current_value
        value = space.get_slot(self.value_slot_name).current_value
        if value is None:
            return None
        rule = ParserRule('', self.section_key, self.uid, None)
        match = rule.find_match(sensors_data)
        if match is not None:
            feedback = Driver.get_current().act(match['section_key'], match['device_key'], self.property_endpoint, self.property_name, value)
            if self.feedback_slot_name is not None:
                space.get_slot(self.feedback_slot_name).current_value = feedback
