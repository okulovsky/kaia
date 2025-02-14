from typing import *
from kaia.kaia import IKaiaSkill, TimerTick, KaiaContext
from datetime import datetime
from eaglesong import ContextRequest

class NarrationSkill(IKaiaSkill):
    def __init__(self, pause_between_checks_in_seconds: int = 5*60):
        self._last_check: datetime|None = None
        self._pause_between_checks_in_seconds = pause_between_checks_in_seconds

    def should_start(self, input) -> bool:
        if not isinstance(input, TimerTick):
            return False
        if self._last_check is None:
            self._last_check = input.current_time
            return False
        delta = input.current_time - self._last_check
        if delta.total_seconds() >= self._pause_between_checks_in_seconds:
            return True
        return False

    def should_proceed(self, input) -> bool:
        return False

    def get_name(self) -> str:
        return "Narration"

    def get_runner(self):
        return self.run

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.SingleLine

    def run(self):
        context: KaiaContext = yield ContextRequest()
        yield from context.avatar_api.narration_tick()

