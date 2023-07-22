from typing import *
from .instant_reaction_skill import TelegramInstantReactionSkill
from kaia.eaglesong.drivers.telegram import TgUpdatePackage
from kaia.eaglesong.core import Return, Terminate, Routine
import telegram as tg

class GroupChatbotRoutine(Routine):
    def __init__(self,
                 debug_only: bool,
                 bot_id: int,
                 chat_id: int,
                 skills: List[TelegramInstantReactionSkill]
                 ):
        self.debug_only = debug_only
        self.chat_id = chat_id
        self.skills = skills

    def run(self, context: TgUpdatePackage):
        update = context.update  # type: tg.Update
        if update.effective_chat.id != self.chat_id:
            if self.debug_only:
                yield Return()
            else:
                yield Terminate('Unauthorized')
            return

        for skill in self.skills:
            result = skill.safe_execute(context.update)
            if len(result) > 0:
                for command in result:
                    yield command
                break
