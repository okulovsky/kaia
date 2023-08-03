from typing import *
from enum import Enum
from kaia.eaglesong.core import Context
import logging
import telegram as tg
import json

class TgUpdatePackage:
    class Type(Enum):
        Start = 0
        Text = 1
        Callback = 2
        Timer = 3
        Feedback = 4
        EaglesongFeedback = 5

    def __init__(self, update_type: 'TgUpdatePackage.Type', update, bot):
        self.update_type = update_type
        self.update = update
        self.bot = bot


class TgContext(Context):
    def __init__(self,
                 bridge,
                 chat_id: Optional[int],
                 ):
        self.bridge = bridge
        self.chat_id = chat_id
        self.bot = None #type: Optional[tg.Bot]
        self.update = None #type: Optional[tg.Update]
        self.update_type = None #type: Optional[TgUpdatePackage.Type]
        self.exact_input = None

    def set_input(self, input: TgUpdatePackage):
        self.exact_input = input
        if isinstance(input, TgUpdatePackage):
            self.update_type = input.update_type
            self.update = input.update
            self.bot = input.bot
        else: #it happens when input is set via eaglesong internals, e.g. Automaton/Return
            self.update_type = TgUpdatePackage.Type.EaglesongFeedback
            self.update = input
            self.bot = None

    def get_input(self):
        return self.exact_input

    def get_input_summary(self):
        return dict(update_type=self.update_type.name, update = self.update)



class TgCommandFunctionMock:
    def __init__(self, function_name: str):
        self.function_name = function_name

    def __call__(self, *args, **kwargs):
        return TgCommand(self.function_name, *args, **kwargs)


class TgCommandMock:
    def __getattr__(self, item):
        return TgCommandFunctionMock(item)


class TgCommand:
    def __init__(self, bot_method: str, *args, **kwargs):
        self.bot_method = bot_method
        self.args = args
        self.kwargs = kwargs
        self._ignore_errors = False

    def ignore_errors(self):
        self._ignore_errors = True
        return self

    @staticmethod
    def mock() -> 'tg.Bot':
        return TgCommandMock()


    async def execute(self, bot):
        method = getattr(bot, self.bot_method)
        last_result = None
        if self._ignore_errors:
            try:
                last_result = await method(*self.args, **self.kwargs)
            except:
                pass
        else:
            last_result = await method(*self.args, **self.kwargs)
        return last_result