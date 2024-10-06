from typing import *
from ..core import Translator, Listen
from abc import ABC, abstractmethod

class PartialListenTranslator(Translator, ABC):

    def __init__(self,
                 inner_function,
                 payload_type: Type,
                 generative_input: bool = False,
                 call_input_translate_without_payload: bool = False
                 ):
        self._payload_type = payload_type
        self._last_payload: Any = None
        self._last_listen: Listen|None = None
        self._generative_input = generative_input
        self._call_input_translate_without_payload = call_input_translate_without_payload
        super().__init__(
            inner_function,
            input_generator_translator=self._translate_input,
            output_function_translator=self._translate_output
        )

    @abstractmethod
    def captures_input(self, input):
        pass

    def on_translate_input(self, payload, input):
        return input

    def observe_output(self, payload, output):
        pass

    def _translate_input(self, input: Translator.InputPackage):
        yield
        if not self.captures_input(input.outer_input):
            return input.outer_input
        result = input.outer_input
        if self._last_payload is not None or self._call_input_translate_without_payload:
            if not self._generative_input:
                result = self.on_translate_input(self._last_payload, input.outer_input)
            else:
                result = yield from self.on_translate_input(self._last_payload, input.outer_input)
        self._last_payload = None
        self._last_listen = None
        return result

    def _translate_output(self, output: Translator.OutputPackage):
        if isinstance(output.inner_output, Listen):
            if self._payload_type in output.inner_output:
                self._last_listen = output.inner_output
                self._last_payload = output.inner_output.get(self._payload_type)
                self.observe_output(self._last_payload, output.inner_output)
        return output.inner_output

    def get_last_listen(self) -> Listen|None:
        return self._last_listen

