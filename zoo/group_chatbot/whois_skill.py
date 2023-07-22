from .instant_reaction_skill import *

class WhoIsSkill(TelegramInstantReactionSkill):
    def __init__(self, owner_id: int):
        self.owner_id = owner_id

    def execute(self, update:tg.Update):
        if update.effective_message.text!='Храз, проверь документы':
            return None
        if update.effective_message.reply_to_message is None:
            return None
        if update.effective_message.from_user.id != self.owner_id:
            return TgCommand.mock().send_message(
                update.effective_chat.id,
                'А ты кто такой?',
                reply_to_message_id=update.effective_message.id
            )

        id = update.effective_message.reply_to_message.from_user.id
        return TgCommand.mock().send_message(
            update.effective_chat.id,
            f"Паспорт подозреваемого: {id}",
            reply_to_message_id=update.effective_message.id
            )


