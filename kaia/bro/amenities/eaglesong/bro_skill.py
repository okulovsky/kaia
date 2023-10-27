from ....eaglesong.amenities import menu
from ....eaglesong import core as eac
from ..messenger_queue_controller import MessengerQueueController
from ...core import BroServer, BroClient, Slot, BoolInput, RangeInput
from yo_fluq_ds import Query
from functools import partial

class BroSkill(menu.MenuFolder):
    def __init__(self, client: BroClient):
        self.client = client
        self.queue_manager = MessengerQueueController(client.space.get_name(), client.messenger)
        super(BroSkill, self).__init__(
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

    def send_value(self, slot, value):
        self.queue_manager.send(slot, value)
        yield eac.Return()

    def free_value(self, slot, prompt):
        yield prompt
        input = yield eac.Listen()
        self.queue_manager.send(slot, input)
        yield eac.Return()

    def _create_menu_item_for_slot(self, slot: Slot):
        if isinstance(slot.input, BoolInput):
            return menu.MenuFolder(
                f'Set the slot {slot.name} in the space {self.client.space.get_name()}',
                slot.name,
            ).items(
                menu.FunctionalMenuItem('True', partial(self.send_value, slot, True), False),
                menu.FunctionalMenuItem('False', partial(self.send_value, slot, False), False)
            )
        if isinstance(slot.input, RangeInput):
            return menu.FunctionalMenuItem(
                slot.name,
                partial(self.free_value, slot, f'Set the slot {slot.name}, value from {slot.input.min} to {slot.input.max}'),
                False
            )

    def _get_text(self):
        text = ''

        current = self.client.data_provider.pull()
        if len(current) == 0:
            text+='No data available\n'
        else:
            current = current[-1]

            for key, value in current.items():
                if not self.client.space.get_slot(key).shown:
                    continue
                text+=f'{key}: {value}\n'
        df = self.queue_manager.get_messager_queue_df()

        if df is not None and df.shape[0]!=0:
            text+='\nCommands:\n'
            for row in Query.df(df):
                text+=f'{row["slot"]} -> {row["value"]} ({row["age"]}): {row["status"]}'

        return text


    @staticmethod
    def generate_skill_for_server(server: BroServer, storage, messenger):
        items = []
        for algorithm in server.algorithms:
            client = server.create_client(algorithm, storage, messenger)
            items.append(BroSkill(client))
        return menu.MenuFolder(
            'Choose the skill',
            'Bro',
        ).items(*items)
