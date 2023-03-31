from telegram import Bot

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
    def mock() -> 'Bot':
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