from .common_imports import *
from string import Template

class NotifierSkill(Routine):
    def __init__(self,
                 affected_users: List[int],
                 message_template: Template
                 ):
        self.affected_users = affected_users
        self.message_template = message_template

    def run(self, context: TgContext):
        update = context.update

        if update.effective_user.id not in self.affected_users:
            yield Return()

        yield TgCommand.mock().send_message(
            chat_id = update.effective_chat.id,
            text = self.message_template.substitute(user=update.effective_user.name),
            reply_to_message_id=update.effective_message.id
        )
