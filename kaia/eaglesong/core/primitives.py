from typing import *
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

class IBotInput:
    @staticmethod
    def is_input(obj):
        return isinstance(obj, str) or isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, IBotInput)

    @staticmethod
    def is_content_input(obj):
        return isinstance(obj, str) or isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, IBotContentInput)


class IBotContentInput(IBotInput):
    pass


class IBotOutput:
    @staticmethod
    def is_output(obj):
        return isinstance(obj, str) or isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, IBotOutput)

    @staticmethod
    def is_content_output(obj):
        return isinstance(obj, str) or isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, IBotContentOutput)

    @staticmethod
    def is_control_output(obj):
        return isinstance(obj, str) or isinstance(obj, int) or isinstance(obj, float) or isinstance(obj, IBotControlOutput)


class IBotContentOutput(IBotOutput):
    pass


class IBotControlOutput(IBotOutput):
    pass


class Context(ABC):
    @abstractmethod
    def set_input(self, input):
        pass

    @abstractmethod
    def get_input(self):
        pass


class Return(IBotControlOutput):
    def __init__(self, *return_value):
        if len(return_value) == 0:
            self.return_value = None
        elif len(return_value) == 1:
            self.return_value = return_value[0]
        else:
            self.return_value = return_value


@dataclass
class Terminate(IBotControlOutput):
    message: str


class ListeningExpectations:
    def expect(self, message):
        raise NotImplementedError()


class ListeningListExpectations(ListeningExpectations):
    def __init__(self, options: Iterable):
        self.options = tuple(options)

    def expect(self, message):
        return message in self.options

class ListeningTypeExpectations(ListeningExpectations):
    def __init__(self, types):
        self.types = tuple(types)

    def expect(self, message):
        for t in self.types:
            if isinstance(message, t):
                return True
        return False

class ListeningLambdaExpectations(ListeningExpectations):
    def __init__(self, expectation: Callable):
        self.expectation = expectation

    def expect(self, message):
        return self.expectation(message)


@dataclass
class Listen(IBotControlOutput):
    expectation: Optional[ListeningExpectations] = None

    @staticmethod
    def for_types(*types):
        return Listen(ListeningTypeExpectations(types))

    @staticmethod
    def for_one_of(*options):
        return Listen(ListeningListExpectations(options))

    @staticmethod
    def for_condition(condition):
        return Listen(ListeningLambdaExpectations(condition))


@dataclass
class Delete(IBotContentOutput):
    id: Any


@dataclass
class Options(IBotContentOutput):
    content: Any
    options: Tuple[str,...]

@dataclass
class SelectedOption(IBotContentInput):
    value: str


@dataclass
class TimerTick(IBotInput):
    pass


@dataclass
class BotContext(Context):
    user_id: Any
    input: Any = None
    timestamp: Optional[datetime] = None

    def set_input(self, input):
        self.input = input
        self.timestamp = datetime.now()

    def get_input(self):
        return self.input


@dataclass
class IsThinking(IBotContentOutput):
    pass