from typing import *
from enum import Enum
import logging
import telegram as tg
import json


class TgChannel(Enum):
    Start = 0
    Text = 1
    Callback = 2
    Timer = 3
    Feedback = 4
    Voice = 5

class TgUpdatePackage:
    def __init__(self, channel: TgChannel, update):
        self.channel = channel
        self.update = update


class TgContext:
    def __init__(self,
                 bridge,
                 chat_id: Optional[int],
                 ):
        self.bridge = bridge
        self.chat_id = chat_id
        self.last_massage_channel = None #type: Optional[TgChannel]


class TgCommandFunctionMock:
    def __init__(self, function_name: str):
        self.function_name = function_name

    def __call__(self, *args, **kwargs):
        return TgCommand(self.function_name, *args, **kwargs)


class TgCommandMock:
    def __getattr__(self, item):
        return TgCommandFunctionMock(item)


class TgFunction:
    def __init__(self, awaitable_function, *args, **kwargs):
        self.awaitable_function = awaitable_function
        self.args = args
        self.kwargs = kwargs

    async def execute(self):
        return await self.awaitable_function(*self.args, **self.kwargs)



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