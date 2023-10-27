from typing import *
from kaia.eaglesong.core import ContextRequest
from kaia.eaglesong.drivers.telegram import TgCommand, TgContext
import telegram as tg
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger('group_chat')

class AdminReplySkillLogic(ABC):
    @abstractmethod
    def run(self, context: TgContext, update: tg.Update):
        pass

class AdminReplySkill:
    def __init__(self,
                 owner_id: int,
                 initial_message: str,
                 wrong_owner_reply: str,
                 no_message_reply: str,
                 logic: AdminReplySkillLogic
                 ):
        self.owner_id = owner_id
        self.initial_message = initial_message
        self.wrong_owner_reply = wrong_owner_reply
        self.no_message_reply = no_message_reply
        self.logic = logic


    def __call__(self):
        update = yield None
        context = yield ContextRequest()

        if update.effective_message.text!=self.initial_message:
            return
        logger.info(f'Entered {type(self.logic)}')

        if update.effective_user.id != self.owner_id:
            yield TgCommand.mock().send_message(
                chat_id = update.effective_chat.id,
                text = self.wrong_owner_reply,
                reply_to_message_id=update.effective_message.id
            )
            return
        logger.info('Owner OK')

        if update.effective_message.reply_to_message is None:
            yield TgCommand.mock().send_message(
                chat_id=update.effective_chat.id,
                text=self.no_message_reply,
                reply_to_message_id=update.effective_message.id
            )
            return
        logger.info(f'Message OK')

        yield from self.logic.run(context, update)

