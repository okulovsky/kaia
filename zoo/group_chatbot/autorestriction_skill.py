from typing import *
import telegram as tg
from kaia.eaglesong.drivers.telegram import TgCommand
from datetime import datetime, timedelta
from .instant_reaction_skill import TelegramInstantReactionSkill
import logging
from string import Template

logger = logging.getLogger('group_chatbot')

class AutorestrictionSkill(TelegramInstantReactionSkill):
    def __init__(self,
                 ids_affected: List[int],
                 delay_in_minutes: Optional[int] = None,
                 max_length: Optional[int] = None,
                 too_long_message_template: Optional[Template] = None
                 ):
        self.ids_affected = ids_affected
        self.delay_in_minutes = delay_in_minutes
        self.max_length = max_length
        self.too_long_message_template = too_long_message_template

    def execute(self, update: tg.Update):
        if update.effective_user.id in self.ids_affected:
            logging.info(f'Bad user has sent the message, now is {datetime.now()}, message from {update.effective_message.date}')
            if self.max_length is not None:
                logging.info('Max_length is not None')
                if len(update.effective_message.text) > self.max_length:
                    logging.info('Message is too long, deleting and sending reminder')
                    reply = [TgCommand.mock().delete_message(
                        update.effective_chat.id,
                        update.effective_message.message_id
                    )]
                    if self.too_long_message_template is not None:
                        reply.append(TgCommand.mock().send_message(
                            update.effective_chat.id,
                            self.too_long_message_template.substitute(user=update.effective_user.name)
                        ))
                    return reply
                logging.info('Message is not too long')

            if self.delay_in_minutes is not None:
                logging.info('delay_in_minutes not None. Sending restriction')
                return TgCommand.mock().restrict_chat_member(
                    update.effective_chat.id,
                    update.effective_message.from_user.id,
                    until_date=datetime.now()+timedelta(minutes=self.delay_in_minutes),
                    permissions=tg.ChatPermissions.no_permissions()
                )




