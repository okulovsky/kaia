from eaglesong.core import IAutomaton
from .telegram_interpreters import TelegramInterpreter
from .primitives import TgChannel, TgUpdatePackage, TgContext


from typing import *
import telegram.ext as tge
import telegram as tg
import logging

import traceback
import asyncio

logger = logging.getLogger('eaglesong')





class TelegramDriver:
    def __init__(self,
                 application: tge.Application,
                 automaton_factory: Callable[[TgContext], IAutomaton],
                 log_incoming = False,
                 ignore_exceptions = False
                 ):
        self.application = application
        self.automaton_factory = automaton_factory
        self.log_incoming = log_incoming
        self.ignore_exceptions = ignore_exceptions

        logger.info('Initializing dispatcher')
        self.chats = {} #type: Dict[int,TelegramInterpreter]
        self.busy = {}

        logger.info('Type `Start` is added')
        application.add_handler(tge.CommandHandler("start", TelegramDriver.Wrapper(self, TgChannel.Start).run))
        logger.info('Type `Text` is added')
        application.add_handler(tge.MessageHandler(tge.filters.TEXT | tge.filters.COMMAND, TelegramDriver.Wrapper(self, TgChannel.Text).run))
        logger.info('Type `Audio` is added')
        application.add_handler(tge.MessageHandler(tge.filters.VOICE, TelegramDriver.Wrapper(self, TgChannel.Voice).run))
        logger.info('Type `Callback` is added')
        application.add_handler(tge.CallbackQueryHandler(TelegramDriver.Wrapper(self, TgChannel.Callback).run))



    class Wrapper:
        def __init__(self, bridge, update_type):
            self.bridge = bridge
            self.update_type = update_type


        async def run(self, update: tg.Update, context: tge.CallbackContext):
            await self.bridge.push(self.update_type, update, context)


    async def push(self, channel: TgChannel, tg_update: tg.Update, tg_context: tge.CallbackContext):
        if self.log_incoming:
            logger.info(tg_update.to_json())
        chat_id = tg_update.effective_chat.id
        while chat_id in self.busy:
            await asyncio.sleep(0.1)
        self.busy[chat_id] = True
        logger.info(f'Incoming {channel} from chat_id {chat_id}')
        if channel == TgChannel.Start or chat_id not in self.chats or self.chats[chat_id].has_exited():
            logger.info(f'Requested new session from {chat_id}')
            context = TgContext(self, chat_id)
            self.chats[chat_id] = TelegramInterpreter(
                self.automaton_factory(context),
                tg_context.bot,
                chat_id
            )
        interpreter = self.chats[chat_id]
        try:
            await interpreter.process(TgUpdatePackage(channel, tg_update))
        except:
            logging.error(f'ERROR in Telegram Bot:\n{traceback.format_exc()}')
            if not self.ignore_exceptions:
                del self.chats[chat_id]
        logger.info(f'Processed {chat_id} from chat_id {chat_id}')
        del self.busy[chat_id]


    class Timer:
        def __init__(self,
                     bridge: 'TelegramDriver',
                     automaton_factory: Optional[Callable[[TgContext], IAutomaton]]):
            self.bridge = bridge
            self.automaton_factory = automaton_factory


        async def run(self, context):
            for chat_id in self.bridge.chats:
                if self.bridge.chats[chat_id].has_exited():
                    continue
                if chat_id in self.bridge.busy:
                    continue
                self.bridge.busy[chat_id] = True
                aut = self.bridge.chats[chat_id]
                await aut.process(TgUpdatePackage(TgChannel.Timer, None))
                del self.bridge.busy[chat_id]

    def add_timer(self, name: str, period_in_seconds: Union[int, float], automaton_factory: Optional[Callable[[TgContext], IAutomaton]]):
        self.application.job_queue.run_repeating(
            TelegramDriver.Timer(self, automaton_factory).run,
            period_in_seconds,
            name = name,
        )



