from typing import *
import telegram as tg
from kaia.eaglesong.drivers.telegram import TgCommand
from datetime import datetime, timedelta
from .instant_reaction_skill import TelegramInstantReactionSkill

class AutorestrictionSkill(TelegramInstantReactionSkill):
    def __init__(self,
                 ids_affected: List[int],
                 delay_in_minutes: int
                 ):
        self.ids_affected = ids_affected
        self.delay_in_minutes = delay_in_minutes

    def execute(self, update: tg.Update):
        if update.effective_user.id in self.ids_affected:
            return TgCommand.mock().restrict_chat_member(
                update.effective_chat.id,
                update.effective_message.from_user.id,
                until_date=datetime.now()+timedelta(minutes=self.delay_in_minutes),
                permissions=tg.ChatPermissions.no_permissions()
            )




