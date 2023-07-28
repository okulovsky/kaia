from typing import *
import telegram as tg
from kaia.eaglesong.drivers.telegram import TgCommand
from .instant_reaction_skill import TelegramInstantReactionSkill
from datetime import timedelta, datetime
from string import Template

class BanhammerSkill(TelegramInstantReactionSkill):
    def __init__(self,
                 owner_id: int,
                 initial_message: str,
                 not_owner_message: str,
                 no_user_message: str,
                 report_template: Template,
                 ban_duration_in_days: int
                 ):
        self.owner_id = owner_id
        self.initial_message = initial_message
        self.not_owner_message = not_owner_message
        self.no_user_message = no_user_message
        self.report_template = report_template
        self.ban_duration_in_days = ban_duration_in_days

    def execute(self, update: tg.Update):
        if update.effective_message.text != self.initial_message:
            return None
        if update.effective_user.id != self.owner_id:
            return TgCommand.mock().send_message(
                chat_id=update.effective_chat.id,
                text = self.not_owner_message,
                reply_to_message_id=update.message.id
            )
        if update.message.reply_to_message is None:
            return TgCommand.mock().send_message(
                chat_id=update.effective_chat.id,
                text=self.no_user_message,
                reply_to_message_id=update.message.id
            )
        ban_user = update.effective_message.reply_to_message.from_user
        report = TgCommand.mock().send_message(
            chat_id=update.effective_chat.id,
            text=self.report_template.substitute(user=ban_user.name),
            reply_to_message_id=update.effective_message.reply_to_message.id
        )
        ban = TgCommand.mock().restrict_chat_member(
            update.effective_chat.id,
            ban_user.id,
            until_date=datetime.now()+timedelta(days=self.ban_duration_in_days),
            permissions=tg.ChatPermissions.no_permissions()
        )
        return [
            report,
            ban
        ]


