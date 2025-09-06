from typing import Iterable
from .common import AvatarService, SoundCommand, SoundConfirmation, TickEvent, message_handler
import time

class SoundPlayUnblockerService(AvatarService):
    def __init__(self, time_limit_in_seconds: int = 10):
        self.time_limit_in_seconds = time_limit_in_seconds
        self.message_id_to_time: dict[str,float] = {}

    @message_handler
    def on_sound_command(self, command: SoundCommand) -> None:
        self.message_id_to_time[command.envelop.id] = time.monotonic()

    @message_handler
    def on_sound_confirmation(self, confirmation: SoundConfirmation) -> None:
        for id in confirmation.envelop.confirmation_for:
            if id in self.message_id_to_time:
                del self.message_id_to_time[id]

    @message_handler
    def on_tick(self, tick: TickEvent) -> Iterable[SoundConfirmation]:
        now = time.monotonic()
        for id, tm in list(self.message_id_to_time.items()):
            if now - tm > self.time_limit_in_seconds:
                yield SoundConfirmation(True).as_confirmation_for(id)
                del self.message_id_to_time[id]


    def requires_brainbox(self):
        return False


