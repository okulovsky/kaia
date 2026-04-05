from ...messaging import AvatarClient, IMessage
from ...daemon import (
    SoundLevelReport, StatefulRecorderStateEvent,
    SoundCommand, SoundConfirmation, SystemSoundCommand,
    SoundStartEvent, SoundEvent,
)
from datetime import datetime, timedelta

class DataReader:
    def __init__(self, client: AvatarClient, past_span_in_seconds: int = 10):
        self.client = client.clone().with_types(
            SoundLevelReport, StatefulRecorderStateEvent,
            SoundCommand, SoundConfirmation, SystemSoundCommand,
            SoundStartEvent, SoundEvent,
        )
        self.last_update: datetime|None = None
        self.past_span_in_seconds = past_span_in_seconds
        self.events: list[IMessage] = []

    def update_data(self):
        now = datetime.now()
        window_start = now - timedelta(seconds=self.past_span_in_seconds)
        if self.last_update is None:
            delta = None
        else:
            delta = (now - self.last_update).total_seconds()
        self.last_update = now
        if delta is None or delta > self.past_span_in_seconds:
            self.events = self.client.tail(from_timestamp=window_start)
        else:
            self.events.extend(self.client.pull(timeout_in_seconds=0))

        while len(self.events) > 0 and self.events[0].envelop.timestamp < window_start:
            self.events.pop(0)

