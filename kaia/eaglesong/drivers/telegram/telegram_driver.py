import sys

import telegram

from kaia.eaglesong.core import RoutineBase, Context
from .telegram_interpreters import TelegramInterpreter
from .primitives import TgCommand, TgUpdatePackage, TgContext


from typing import *
import telegram.ext as tge
import telegram as tg
from enum import Enum
import logging

import traceback
import asyncio

logger = logging.getLogger('eaglesong')





class TelegramDriver:
    def __init__(self,
                 application: tge.Application,
                 head_subroutine_factory: Callable[[int], RoutineBase],
                 log_incoming = False
                 ):
        self.application = application
        self.head_subroutine_factory = head_subroutine_factory
        self.log_incoming = log_incoming

        logger.info('Initializing dispatcher')
        self.chats = {} #type: Dict[int,TelegramInterpreter]
        self.busy = {}

        logger.info('Type `Start` is added')
        application.add_handler(tge.CommandHandler("start", TelegramDriver.Wrapper(self, TgUpdatePackage.Type.Start).run))
        logger.info('Type `Text` is added')
        application.add_handler(tge.MessageHandler(tge.filters.TEXT | tge.filters.COMMAND, TelegramDriver.Wrapper(self, TgUpdatePackage.Type.Text).run))
        logger.info('Type `Callback` is added')
        application.add_handler(tge.CallbackQueryHandler(TelegramDriver.Wrapper(self, TgUpdatePackage.Type.Callback).run))


    class Wrapper:
        def __init__(self, bridge, update_type):
            self.bridge = bridge
            self.update_type = update_type


        async def run(self, update: tg.Update, context: tge.CallbackContext):
            await self.bridge.push(self.update_type, update, context)


    async def push(self, update_type: TgUpdatePackage.Type, tg_update: tg.Update, context: tge.CallbackContext):
        if self.log_incoming:
            logger.info(tg_update.to_json())
        chat_id = tg_update.effective_chat.id
        while chat_id in self.busy:
            await asyncio.sleep(0.1)
        self.busy[chat_id] = True
        logger.info(f'Incoming {update_type} from chat_id {chat_id}')
        if update_type == TgUpdatePackage.Type.Start or chat_id not in self.chats or self.chats[chat_id].has_exited():
            logger.info(f'Requested new session from {chat_id}')
            self.chats[chat_id] = TelegramInterpreter(self.head_subroutine_factory(chat_id), TgContext(self, chat_id))
        aut = self.chats[chat_id]
        try:
            await aut.process(TgUpdatePackage(update_type, tg_update, context.bot))
        except:
            logging.error(f'ERROR in Telegram Bot:\n{traceback.format_exc()}')
            del self.chats[chat_id]
        logger.info(f'Processed {update_type} from chat_id {chat_id}')
        del self.busy[chat_id]


    class Timer:
        def __init__(self, bridge: 'TelegramDriver', routine_factory: Optional[Callable[[], RoutineBase]]):
            self.bridge = bridge
            self.routine_factory = routine_factory


        async def run(self, context):
            for chat_id in self.bridge.chats:
                if self.bridge.chats[chat_id].has_exited():
                    continue
                if chat_id in self.bridge.busy:
                    continue
                self.bridge.busy[chat_id] = True
                if self.routine_factory is None:
                    aut = self.bridge.chats[chat_id]
                else:
                    bot_context = TgContext(self.bridge, chat_id)
                    aut = TelegramInterpreter(self.routine_factory(), bot_context)
                await aut.process(TgUpdatePackage(TgUpdatePackage.Type.Timer, None, context.bot))
                del self.bridge.busy[chat_id]

    def add_timer(self, name: str, period_in_seconds: Union[int, float], routine_factory: Optional[Callable[[], RoutineBase]]):
        self.application.job_queue.run_repeating(
            TelegramDriver.Timer(self, routine_factory).run,
            period_in_seconds,
            name = name,
        )



