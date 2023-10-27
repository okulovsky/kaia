from .common_imports import *

from dataclasses import dataclass

def default_message_factory(user_to_attempts: Dict[str,int]):
    return f'{", ".join(user_to_attempts.keys())} tried to send long messages, {sum(user_to_attempts.values())} in total'

class LongMessagesRestricter:
    def __init__(self,
                 ids_affected: List[int],
                 max_length: int,
                 message_factory: Optional[Callable[[Dict[str,int]], str]] = None,
                 pause_between_messages: Optional[int] = None
                 ):
        self.ids_affected = ids_affected
        self.max_length = max_length
        self.message_factory = message_factory
        self.memory = {} #type: Dict[str, int]
        self.last_notification_sent = None
        self.message_counter = 0
        self.pause_between_messages = pause_between_messages
        self.last_message_id = None


    def __call__(self):
        update = yield None

        self.message_counter+=1

        if update.effective_user.id not in self.ids_affected:
            return

        if len(update.effective_message.text) <= self.max_length:
            return

        yield TgCommand.mock().delete_message(
            chat_id = update.effective_chat.id,
            message_id = update.effective_message.message_id
        )
        self.message_counter -= 1

        if self.message_factory is None:
            return

        can_post = (
                self.pause_between_messages is None
                or self.last_notification_sent is None
                or self.message_counter - self.last_notification_sent >= self.pause_between_messages
        )

        if can_post:
            self.memory = {}

        username = f'{update.effective_user.name} ({update.effective_user.id})'
        if username not in self.memory:
            self.memory[username] = 0
        self.memory[username] += 1

        message = self.message_factory(self.memory)

        if can_post:
            sent_message = yield TgCommand.mock().send_message(
                chat_id=update.effective_chat.id,
                text=message
            )
            self.last_message_id = sent_message.message_id
            self.last_notification_sent = self.message_counter
        elif self.last_message_id is not None:
            yield TgCommand.mock().edit_message_text(
                text = message,
                chat_id = update.effective_chat.id,
                message_id = self.last_message_id
            )







