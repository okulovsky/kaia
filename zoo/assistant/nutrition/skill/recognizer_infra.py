from enum import Enum
from dataclasses import dataclass
from kaia.eaglesong.core import Translator, Return
from kaia.kaia.translators import Listen
from abc import ABC, abstractmethod

class Message:
    class Type(Enum):
        Cancel = 0
        Yes = 1
        No = 2
        FoodRecord = 3
        Name = 4
        Number = 5

    type: 'Message.Type'
    name: str|None = None



class Recognizer(ABC):
    def __init__(self, allowed_types: list[Message.Type] = None):
        self.allowed_types = allowed_types

    def __call__(self, s: str):
        return self.recognize(s)

    @abstractmethod
    def recognize(self, s: str):
        pass



class RecognitionWrap(Translator):
    def __init__(self, inner_function):
        super().__init__(
            inner_function,
            input_generator_translator=self.translate_input,
            output_function_translator=self.translate_output
        )

    def translate_output(self, output: Translator.OutputPackage):
        if isinstance(output.inner_output, Listen):
            self.last_listen = output.inner_output
            if isinstance(output.inner_output.recognizer, Recognizer):
                self.allowed_types = output.inner_output.recognizer
            else:
                self.allowed_types = None
        return output.inner_output

    def translate_input(self, input: Translator.InputPackage):
        if not isinstance(input, Message):
            yield input
        else:
            if input.type == Message.Type.Cancel:
                raise Return()
            if self.allowed_types is not None and input.type in self.allowed_types:
                yield f"Unexpected input {input.type.name}, please repeat."
                yield self.last_listen
