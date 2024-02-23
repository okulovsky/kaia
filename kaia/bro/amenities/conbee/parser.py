from typing import *
from ...core import ISpace, Slot
import json


class ParserRule:
    def __init__(self,
                 slot: Union[str, Slot],
                 section: Optional[str],
                 uid: str,
                 transform: Optional[Callable]
                 ):
        self.name = Slot.slotname(slot)
        self.section = section
        self.uid = uid
        self.transform = transform

    def find_match(self, data):
        for section_key, section_data in data.items():
            for device_key, data in section_data.items():
                if self.section is not None and self.section != section_key:
                    continue
                if data.get('uniqueid', '') != self.uid:
                    continue
                return dict(section_key = section_key, device_key = device_key, data = data)
        else:
            return None




class Parser:
    def __init__(self,
                 source_slot: Union[Slot, str],
                 last_update_slot: Union[Slot,str,None] = None,
                 ):
        self.source_slot = Slot.slotname(source_slot)
        self.last_update_slot = Slot.slotname(last_update_slot)
        self.rules = [] #type: List[ParserRule]

    def add_rule(self,
                 name: Union[str, Slot],
                 section: str,
                 uid: str,
                 transform: Optional[Callable] = None,
                 ) -> 'Parser':
        self.rules.append(ParserRule(name,section,uid,transform))
        return self

    def __call__(self, space: ISpace):
        all_data = space.get_slot(self.source_slot).current_value
        for rule in self.rules:
            match = rule.find_match(all_data)
            if match is not None:
                space.get_slot(rule.name).current_value = rule.transform(match['data'])





