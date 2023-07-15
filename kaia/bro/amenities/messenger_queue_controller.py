from ...infra import Message, IMessenger
import datetime
from yo_fluq_ds import Query
import pandas as pd
from functools import partial


class MessengerQueueController:
    def __init__(self, space_name: str, messenger: IMessenger, keep_updates_for_seconds: int = 10):
        self.space_name = space_name
        self.messenger = messenger
        self.closing_times = {}
        self.keep_updates_for_seconds = keep_updates_for_seconds

    def send(self, slot, value):
        id = self.messenger.add(value, 'to', self.space_name, 'set_field', slot.name)
        self.closing_times[id] = None
        return id

    def has_updates(self):
        return len(self.closing_times) > 0

    def _message_to_record(self, now, message: Message):
        result = []
        result.append(message.tags[3])
        result.append(message.payload)
        seconds = int((now - message.date_posted).total_seconds())
        result.append(str(seconds) + ' sec ago')
        status = '?'
        if not message.open:
            if message.result is None:
                status = '✔'
            else:
                status = message.result
        else:
            status = '⌛'
        result.append(status)
        return result

    def get_messager_queue_df(self):
        now = datetime.datetime.now()
        messages = IMessenger.Query(tags=['to', self.space_name, 'set_field']).query(self.messenger)
        messages = [m for m in messages if m.id in self.closing_times]

        for m in messages:
            if not m.open and self.closing_times[m.id] is None:
                self.closing_times[m.id] = now

        messages = (Query
                    .en(messages)
                    .where(lambda z: self.closing_times[z.id] is None or (now - self.closing_times[z.id]).total_seconds() < self.keep_updates_for_seconds)
                    .order_by_descending(lambda z: z.date_posted)
                    .select(lambda z: self._message_to_record(now, z))
                    .to_list()
                    )
        df = pd.DataFrame(messages, columns=['slot', 'value', 'age', 'status'])
        return df
