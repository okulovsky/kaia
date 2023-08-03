from typing import *
from .admin_reply import AdminReplySkillLogic, TgContext, tg, logger, TgCommand
from string import Template

class Whois(AdminReplySkillLogic):
    def __init__(self,
                 reply: Template,
                 list_template: Optional[Template] = None,
                 lists: Optional[Dict[str,Dict[str,Any]]] = None,
                 ):
        self.reply = reply
        self.list_template = list_template
        self.lists = lists

    def run(self, context: TgContext, update: tg.Update):
        id = update.effective_message.reply_to_message.from_user.id
        logger.info(f'Message OK, id {id}')

        message = self.reply.substitute(user_id=id)

        if self.lists is not None and self.list_template is not None:
            logger.info('checking lists')
            for name, userlist in self.lists.items():
                if str(id) in userlist:
                    logger.info(f'Found in list {name}')
                    message += '\n' + self.list_template.substitute(name=name, value=userlist[str(id)])

        yield TgCommand.mock().send_message(
            chat_id=update.effective_chat.id,
            text=message,
            reply_to_message_id=update.effective_message.id
        )

