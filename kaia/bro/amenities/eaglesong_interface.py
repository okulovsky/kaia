from ....eaglesong.amenities import menu
from ....eaglesong import core as eac
from ..messenger_queue_controller import MessengerQueueController
from ...core import BroClient, ISpace, Slot, BoolInput, RangeInput
from functools import partial

class Sender:
    def __init__(self, client: BroClient):
        self.client = client

    def send_value(self, slot, value):
        self.client.messenger.add(value,'to',self.client.space.get_name(),'set_field',slot.name)

    def functional(self, slot, value):
        return partial(self.send_value, slot, value)


class ServiceSkill(menu.MenuFolder):
    def __init__(self, client: BroClient):
        self.client = client
        self.queue_manager = MessengerQueueController(client.space.get_name(), client.messenger)
        super(ServiceSkill, self).__init__(
            self._get_text,
            client.space.get_name(),
            True
        )
        menu_items = []
        for slot in client.space.get_slots():
            item = self._create_menu_item_for_slot(slot)
            if item is None:
                continue
            menu_items.append(item)
        self.items(*menu_items)

    def send_value(self, c, slot, value):
        self.queue_manager.send(slot, value)
        yield eac.Return()

    def free_value(self, c, slot, prompt):
        yield prompt
        yield eac.Listen()
        self.queue_manager.send(slot, c.input)
        yield eac.Return()

    def _create_menu_item_for_slot(self, slot: Slot):
        if isinstance(slot.input, BoolInput):
            return menu.MenuFolder(
                f'Set the slot {slot.name} in the space {self.client.space.get_name()}',
                slot.name,
            ).items(
                menu.FunctionalMenuItem('True', eac.Subroutine(self.send_value, slot, True)),
                menu.FunctionalMenuItem('False', eac.Subroutine(self.send_value, slot, False))
            )
        if isinstance(slot.input, RangeInput):
            return menu.Subroutine(self.free_value, slot, f'Set the slot {slot.name}, value from {slot.input.min} to {slot.input.max}')

    def _get_text(self):
        current = self.client.data_provider.pull()
        if len(current) == 0:
            return 'No data available'
        current = current[-1]
        text = ''
        for key, value in current.items():
            if not self.client.space.get_slot(key).shown:
                continue
            text+=f'{key}: {value}\n'
        return text

