import datetime
from typing import *

import pandas as pd

from ....infra.comm import IMessenger, Message
from ...core import Slot, RangeInput, BoolInput
from ..messenger_queue_controller import MessengerQueueController
import gradio as gr
import time
from enum import Enum
from yo_fluq_ds import Query

class SendingStatus(Enum):
    no = 0
    in_process = 1
    failure = 2
    success = 3


class Configurer:
    def __init__(self,
                 space_name: str,
                 pull: Callable,
                 messenger: IMessenger,
                 slots: List[Slot]):
        self.space_name = space_name
        self.messenger = messenger
        self.slots = slots
        self.controlled_slots = None
        self.pull = pull
        self.sending_status = SendingStatus.no
        self.queue_controller = MessengerQueueController(self.space_name, self.messenger)


    def _create_controls(self, slot):
        if slot.input is None:
            return None
        label = slot.name
        if slot.hint is not None:
            label = slot.hint

        if isinstance(slot.input, RangeInput):
            return gr.Slider(
                minimum=slot.input.min,
                maximum=slot.input.max,
                label=label,
                visible=False
            )
        if isinstance(slot.input, BoolInput):
            return gr.Radio(
                choices=[True, False],
                label = label,
                visible = False
            )

    def generate_interface(self):
        configure = gr.Button('Configure')
        update = gr.Button('Update', visible=False)
        cancel = gr.Button('Cancel', visible=False)
        sliders = []
        self.controlled_slots = []
        for slot in self.slots:
            control = self._create_controls(slot)
            if control is not None:
                self.controlled_slots.append(slot)
                sliders.append(control)
        dataframe = gr.DataFrame(visible=False, value=self._get_df, every=1)
        all_settings = [configure, update, cancel, dataframe] + sliders
        configure.click(self._cm_configure, inputs=[configure], outputs=all_settings)
        update.click(self._cm_update, inputs=sliders, outputs=all_settings)
        cancel.click(self._cm_cancel, inputs=[cancel], outputs = all_settings)


    def _cm_configure(self, *args):
        current = self.pull()
        if len(current)==0:
            return self._reply(True, False, False)
        current = current[-1]
        values = [current[slot.name] for slot in self.controlled_slots]
        return self._reply(False, True, True, controls_values=values)

    def _cm_update(self, *values):
        current = self.pull()
        if len(current) == 0:
            return self._reply(True, False, False)
        current = current[-1]
        for i, slot in enumerate(self.controlled_slots):
            if values[i] == current[slot.name]:
                continue
            if values[i] is None:
                continue
            self.queue_controller.send(slot, values[i])
        return self._reply(True, False, False)

    def _cm_cancel(self, *args):
        return self._reply(True, False, False)

    def _get_df(self):
        if not self.queue_controller.has_updates():
            return None
        df = self.queue_controller.get_messager_queue_df()
        if df.shape[0] == 0:
            return gr.update(visible = False, value = None)
        return df


    def _reply(self, config, update, controls, controls_values = None):
        result = []
        result.append(gr.update(visible=config))
        result.append(gr.update(visible=update))
        result.append(gr.update(visible=update))
        result.append(gr.update(visible=self.queue_controller.has_updates()))
        for i, c in enumerate(self.controlled_slots):
            kwargs = dict(visible=controls)
            if controls_values is not None:
                kwargs['value'] = controls_values[i]
            result.append(gr.update(**kwargs))
        return result

