from typing import *
from kaia.eaglesong.core import Interpreter, Return, Terminate, Listen, IAutomaton
from .primitives import TgCommand, TgUpdatePackage, TgChannel, TgFunction
import telegram as tg

class TelegramInterpreter(Interpreter):
    def __init__(self, automaton: IAutomaton, bot: tg.Bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id
        super(TelegramInterpreter, self).__init__(automaton)
        self.handle_type_async(Return, self._process_return)
        self.handle_type_async(Listen, self._process_listen)
        self.handle_type_async(Terminate, self._process_terminate)
        self.handle_type_async(TgCommand, self._process_tg_command)
        self.handle_type_async(TgFunction, self._process_tg_function)

    async def _process_listen(self, response):
        return Interpreter.interrupt_cycle()

    async def _process_return(self, response):
        return Interpreter.reset_automaton()

    async def _process_terminate(self, response: Terminate):
        await self.bot.send_message(
            self.chat_id,
            f'Error when handling the chat:\n\n{response.message}\n\nTo restart the bot, execute /start command or write any message'
        )
        return Interpreter.reset_automaton()

    async def _process_tg_command(self, response: TgCommand):
        last_return = await response.execute(self.bot)
        returned_value = TgUpdatePackage(TgChannel.Feedback, last_return)
        return Interpreter.continue_cycle(returned_value)

    async def _process_tg_function(self, response: TgFunction):
        returned = await response.execute()
        returned_value = TgUpdatePackage(TgChannel.Feedback, returned)
        return Interpreter.continue_cycle(returned_value)

    async def process(self, item):
        await self._async_process(item)









