import sys
from typing import *
from ..core import ISpace, IUnit, Slot
from ...infra.comm import IMessenger


class SettingsReader(IUnit):
    def run(self, space: ISpace, messenger: IMessenger):
        messages = IMessenger.Query(open=True, tags=['to', space.get_name(), 'set_field']).query(messenger)
        slot_dict = space.get_slots_as_dict()
        for message in messages:
            if len(message.tags) != 4:
                messenger.close(message.id, 'Must be exactly 4 tags')
                continue
            slot_name = message.tags[3]
            if slot_name not in slot_dict:
                messenger.close(message.id, f'Field {slot_name} not in space {space.get_name()}')
                continue
            slot = slot_dict[slot_name]
            if slot.input is None:
                messenger.close(message.id, f'Field {slot_name} in space {space.get_name()} is not externally writable')
                continue
            try:
                validated = slot.input.validate(message.payload)
                reason = None
            except:
                validated = None
                _, reason, __ = sys.exc_info()
            if validated is None:
                messenger.close(message.id, f'Value {message.payload} is wrong for slot {slot_name} in space {space.get_name()}\n{reason}')
                continue
            slot.current_value = validated
            messenger.close(message.id, None)


class FieldNotNullNotifier(IUnit):
    def __init__(self, slot: Union[str, Slot]):
        self.slot_name = Slot.slotname(slot)

    def run(self, space: ISpace, messenger: IMessenger):
        slot = space.get_slot(self.slot_name)
        if slot.current_value is not None:
            value = space.get_current_values_as_dict()
            messenger.add(value, 'from', space.get_name(), 'notification', 'not_null', self.slot_name)

