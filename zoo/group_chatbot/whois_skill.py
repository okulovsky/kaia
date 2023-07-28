from .instant_reaction_skill import *
from string import Template
import logging

logger = logging.getLogger('group_chatbot')

class WhoIsSkill(TelegramInstantReactionSkill):
    def __init__(self,
                 owner_id: int,
                 initial_message: str,
                 wrong_owner_reply: str,
                 no_message_reply: str,
                 reply: Template,
                 list_template: Optional[Template] = None,
                 lists: Optional[Dict[str,Dict[str,Any]]] = None,
                 ):
        self.owner_id = owner_id
        self.initial_message = initial_message
        self.wrong_owner_reply = wrong_owner_reply
        self.no_message_reply = no_message_reply
        self.reply = reply
        self.lists = lists
        self.list_template = list_template

    def execute(self, update:tg.Update):
        if update.effective_message.text!=self.initial_message:
            return None
        logging.info('Whois requested')
        if update.effective_message.from_user.id != self.owner_id:
            return TgCommand.mock().send_message(
                update.effective_chat.id,
                self.wrong_owner_reply,
                reply_to_message_id=update.effective_message.id
            )
        logging.info('Owner OK')
        if update.effective_message.reply_to_message is None:
            if update.effective_message.from_user.id != self.owner_id:
                return TgCommand.mock().send_message(
                    update.effective_chat.id,
                    self.no_message_reply,
                    reply_to_message_id=update.effective_message.id
                )
        id = update.effective_message.reply_to_message.from_user.id
        logging.info(f'Message ok, id {id}')
        message = self.reply.substitute(user_id = id)

        if self.lists is not None and self.list_template is not None:
            logging.info('checking lists')
            for name, userlist in self.lists.items():
                if str(id) in userlist:
                    logging.info(f'Found in list {name}')
                    message+='\n'+self.list_template.substitute(name=name, value=userlist[str(id)])

        return TgCommand.mock().send_message(
            update.effective_chat.id,
            message,
            reply_to_message_id=update.effective_message.id
            )


