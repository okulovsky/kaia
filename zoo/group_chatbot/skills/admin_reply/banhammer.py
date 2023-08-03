from typing import *
from .admin_reply import AdminReplySkillLogic, TgContext, tg, TgCommand
from string import Template
from datetime import datetime, timedelta

class Banhammer(AdminReplySkillLogic):
    def __init__(self,
                 report_template: Template,
                 ban_duration_in_days: int,
                 current_time_factory: Callable[[], datetime] = datetime.now
                 ):
        self.report_template = report_template
        self.ban_duration_in_days = ban_duration_in_days
        self.current_time_factory = current_time_factory

    def run(self, context: TgContext, update: tg.Update):
        ban_user = update.effective_message.reply_to_message.from_user

        yield TgCommand.mock().send_message(
            chat_id=update.effective_chat.id,
            text=self.report_template.substitute(user=ban_user.name),
            reply_to_message_id=update.effective_message.reply_to_message.id
        )

        yield TgCommand.mock().restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=ban_user.id,
            until_date=self.current_time_factory() + timedelta(days=self.ban_duration_in_days),
            permissions=tg.ChatPermissions.no_permissions()
        )
