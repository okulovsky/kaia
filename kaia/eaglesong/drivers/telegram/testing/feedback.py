from ..primitives import TgCommand
from .....infra import Obj

class TelegramReplayGenerator:
    def __init__(self):
        self.current_message_id = 10000

    def __call__(self, v):
        if not isinstance(v, TgCommand):
            return None
        if not v.bot_method in ['send_message']:
            return None
        self.current_message_id += 1
        return Obj(message_id = self.current_message_id)