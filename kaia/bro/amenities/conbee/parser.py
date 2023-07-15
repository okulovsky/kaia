from typing import *
from ...core import ISpace, Slot
import json


class ParserRule:
    def __init__(self,
                 slot: Union[str, Slot],
                 section,
                 uid,
                 transform
                 ):
        self.name = Slot.slotname(slot)
        self.section = section
        self.uid = uid
        self.transform = transform

class Parser:
    def __init__(self,
                 source_slot: Union[Slot, str],
                 last_update_slot: Union[Slot,str,None] = None,
                 ):
        self.source_slot = Slot.slotname(source_slot)
        self.last_update_slot = Slot.slotname(last_update_slot)
        self.rules = []

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
        for section_key, section_data in all_data.items():
            for data in section_data.values():
                for rule in self.rules:
                    if rule.section!=section_key:
                        continue
                    if data.get('uniqueid', '') != rule.uid:
                        continue
                    if rule.transform is not None:
                        space.get_slot(rule.name).current_value = rule.transform(data)



