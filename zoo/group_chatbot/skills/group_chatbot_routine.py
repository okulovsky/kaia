from kaia.eaglesong.core import Routine, RoutineBase, Terminate
from kaia.eaglesong.drivers.telegram import TgContext

class GroupChatbotRoutine(Routine):
    def __init__(self,
                 group_chat_id: int,
                 group_skill: RoutineBase
                 ):
        self.group_chat_id = group_chat_id
        self.group_skill = group_skill

    def run(self, context: TgContext):
        if context.chat_id != self.group_chat_id:
            yield Terminate('Unauthorized')
        yield self.group_skill
