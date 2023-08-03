from ..primitives import TgCommand

class TgCommandKwargsSubsetValidator:
    def __init__(self, bot_method, **kwargs):
        self.kwargs = kwargs
        self.bot_method = bot_method

    def __call__(self, command: TgCommand):
        if self.bot_method != command.bot_method:
            raise ValueError(f'Expected bot_method {self.bot_method}, actual {command.bot_method}')
        for key, value in self.kwargs.items():
            if key not in command.kwargs:
                raise ValueError(f'Key {key} expected, but not present')
            if value!=command.kwargs[key]:
                raise ValueError(f'Value on the key {key} is expected {value}, but was {command.kwargs[key]}')
        return True


class TgCommandValidator:
    def __init__(self, bot_method, *args, **kwargs):
        self.bot_method = bot_method
        self.args = args
        self.kwargs = kwargs

    def __call__(self, command: TgCommand):
        if self.bot_method != command.bot_method:
            raise ValueError(f'Expected bot_method {self.bot_method}, actual {command.bot_method}')
        if self.args != command.args:
            raise ValueError(f'Expected args {self.args}, actial {command.args}')
        expected_keys = tuple(sorted(self.kwargs))
        actualy_keys = tuple(sorted(command.kwargs))
        if expected_keys != actualy_keys:
            raise ValueError(f'Expected kwargs keys {expected_keys}, actial {actualy_keys}')
        for key in expected_keys:
            if self.kwargs[key] != command.kwargs[key]:
                raise ValueError(f'Kwarg key {key}: expected {self.kwargs[key]}, actual {command.kwargs[key]}')
        return True

class TgCommandValidatorFunctionMock:
    def __init__(self, function_name: str):
        self.function_name = function_name

    def __call__(self, *args, **kwargs):
        return TgCommandValidator(self.function_name, *args, **kwargs)

    def kwargs_subset(self, **kwargs):
        return TgCommandKwargsSubsetValidator(self.function_name, **kwargs)


class TgCommandValidatorMock:
    def __getattr__(self, item):
        return TgCommandValidatorFunctionMock(item)

