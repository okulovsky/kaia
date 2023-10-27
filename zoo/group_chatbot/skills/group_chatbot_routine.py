from typing import *
from kaia.eaglesong.core import Terminate, ContextRequest
from kaia.eaglesong.drivers.telegram import TgContext

class GroupChatbotRoutine:
    def __init__(self,
                 group_chat_id: int,
                 group_skill: Callable
                 ):
        self.group_chat_id = group_chat_id
        self.group_skill = group_skill

    def __call__(self):
        context = yield ContextRequest()
        if context.chat_id != self.group_chat_id:
            raise Terminate('Unauthorized')
        yield from self.group_skill()
