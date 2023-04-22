from typing import *
from kaia.eaglesong.core import Interpreter, Return, Terminate, Listen, Automaton, Subroutine
from .primitives import TgCommand, TgUpdatePackage, TgContext

class TelegramInterpreter(Interpreter):
    def __init__(self, subtourine, context: TgContext):
        super(TelegramInterpreter, self).__init__(subtourine, context, True)
        self.handle_type_async(Return, self._process_return)
        self.handle_type_async(Listen, self._process_listen)
        self.handle_type_async(Terminate, self._process_terminate)
        self.handle_type_async(TgCommand, self._process_tg_command)

    async def _process_listen(self, response):
        return Interpreter.interrupt_cycle()

    async def _process_return(self, response):
        return Interpreter.reset_automaton()

    async def _process_terminate(self, response: Terminate):
        await self.context.bot.send_message(
            self.context.chat_id,
            f'Error when handling the chat:\n\n{response.message}\n\nTo restart the bot, execute /start command or write any message'
        )
        return Interpreter.reset_automaton()

    async def _process_tg_command(self, response: TgCommand):
        last_return = await response.execute(self.context.bot)
        self.context.set_input(TgUpdatePackage(TgUpdatePackage.Type.Feedback, last_return, self.context.bot))
        return Interpreter.continue_cycle()

    async def process(self, item):
        self.context.set_input(item)
        await self._async_process()











