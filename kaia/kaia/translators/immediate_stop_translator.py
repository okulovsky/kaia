from .partial_listen_translator import PartialListenTranslator
from eaglesong import Return
from eaglesong.templates import Template, Utterance

class ImmediateStopListenPayload:
    def __init__(self, template: Template):
        self.template = template


class ImmediateStopTranslator(PartialListenTranslator):
    def __init__(self, inner_function):
        super().__init__(inner_function, ImmediateStopListenPayload)

    def captures_input(self, input):
        return isinstance(input, Utterance)

    def on_translate_input(self, payload: ImmediateStopListenPayload, input):
        if input in payload.template:
            raise Return()
        return input




