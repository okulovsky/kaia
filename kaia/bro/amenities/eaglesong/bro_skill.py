import io

import plotly.graph_objs

from ....eaglesong.amenities import menu
from ....eaglesong import core as eac
from ..messenger_queue_controller import MessengerQueueController
from ...core import BroServer, BroClient, Slot, BoolInput, RangeInput, SetInput, BroAlgorithm
from yo_fluq_ds import Query
from functools import partial
import pandas as pd

class BroSkill(menu.MenuFolder):
    def __init__(self, client: BroClient, algorithm: BroAlgorithm):
        self.client = client
        self.algorithm = algorithm
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
        if self.algorithm.presentation.plot_function is not None:
            menu_items.append(menu.FunctionalMenuItem('📈', self._cm_plot, True))
        self.items(*menu_items)

    def _cm_plot(self):
        data = pd.DataFrame(self.client.data_provider.pull())
        plot_obj = self.algorithm.presentation.plot_function.draw(data, self.client.space.get_name())
        if isinstance(plot_obj, plotly.graph_objs.Figure):
            stream = io.BytesIO()
            plot_obj.write_image(stream)
            yield eac.Image(stream.getvalue(), None)
        else:
            yield f"Unknown plot object {plot_obj}"



    def send_value(self, slot, value):
        self.queue_manager.send(slot, value)
        yield eac.Return()

    def free_value(self, slot, prompt, transform = None):
        yield prompt
        input = yield eac.Listen()
        if transform is not None:
            input = transform(input)
        self.queue_manager.send(slot, input)
        yield eac.Return()

    def _create_menu_item_for_slot(self, slot: Slot):
        if isinstance(slot.input, SetInput):
            menu_items = [menu.FunctionalMenuItem(str(v), partial(self.send_value, slot, v), False) for v in slot.input.values]
            return menu.MenuFolder(
                f'Set the slot {slot.name} in the space {self.client.space.get_name()}',
                slot.name,
            ).items(*menu_items)
        if isinstance(slot.input, RangeInput):
            return menu.FunctionalMenuItem(
                slot.name,
                partial(self.free_value, slot, f'Set the slot {slot.name}, value from {slot.input.min} to {slot.input.max}', float),
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
            items.append(BroSkill(client, algorithm))
        return menu.MenuFolder(
            'Choose the skill',
            'Bro',
        ).items(*items)
