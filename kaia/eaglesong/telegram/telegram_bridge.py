from ..arch import AbstractAutomaton, Return, Listen, Terminate
from .tg_command import TgCommand


from typing import *
import telegram.ext as tge
import telegram as tg
from enum import Enum
import logging

import traceback

logger = logging.getLogger('eaglesong')

class TgUpdate:
    class Type(Enum):
        Start = 0
        Text = 1
        Callback = 2

    def __init__(self,
                 chat_id: int,
                 type: 'TgUpdate.Type',
                 update: tg.Update,
                 context: tge.CallbackContext):
        self.chat_id = chat_id
        self.type = type
        self.update = update
        self.context = context
        self.last_return = None
        self.is_continuation = False


class TelegramBridge:
    def __init__(self,
                 application: tge.Application,
                 head_automaton_factory: Callable[[tg.Update], AbstractAutomaton],
                 log_incoming = False
                 ):
        self.application = application
        self.head_automaton_factory = head_automaton_factory
        self.log_incoming = log_incoming

        logger.info('Initializing dispatcher')
        self.chats = {}
        self.slots = {}


        logger.info('Type `Start` is added')
        application.add_handler(tge.CommandHandler("start", TelegramBridge.Wrapper(self, TgUpdate.Type.Start).run))
        logger.info('Type `Text` is added')
        application.add_handler(tge.MessageHandler(tge.filters.TEXT | tge.filters.COMMAND, TelegramBridge.Wrapper(self, TgUpdate.Type.Text).run))
        logger.info('Type `Callback` is added')
        application.add_handler(tge.CallbackQueryHandler(TelegramBridge.Wrapper(self, TgUpdate.Type.Callback).run))


    class Wrapper:
        def __init__(self, bridge, update_type):
            self.bridge = bridge
            self.update_type = update_type


        async def run(self, update: tg.Update, context: tge.CallbackContext):
            await self.bridge.push(self.update_type, update, context)

    async def push(self, update_type: TgUpdate.Type, tg_update: tg.Update, context: tge.CallbackContext):
        if self.log_incoming:
            logger.info(tg_update.to_json())
        chat_id = tg_update.effective_chat.id
        logger.info(f'Incoming {update_type} from chat_id {chat_id}')
        if update_type == TgUpdate.Type.Start or chat_id not in self.chats:
            logger.info(f'Requested new session from {chat_id}')
            self.chats[chat_id] = self.head_automaton_factory(tg_update)

        update = TgUpdate(chat_id, update_type, tg_update, context)
        aut = self.chats[chat_id]

        while True:
            result = aut.process(update)
            if isinstance(result, Return):
                del self.chats[chat_id]
                break
            if isinstance(result, Terminate):
                await context.bot.send_message(chat_id, f'Error when handling the chat:\n\n{result.message}\n\nTo restart the bot, execute /start command or write any message')
                del self.chats[chat_id]
                break
            elif isinstance(result, Listen):
                break
            elif isinstance(result, TgCommand):
                update.last_return = await result.execute(tg_update.get_bot(), chat_id)
                update.is_continuation = True
            else:
                raise ValueError(f'Unexpected type {type(result)} of the command')

        logger.info(f'Processed {update_type} from chat_id {chat_id}')








