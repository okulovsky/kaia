from kaia.dub import Template, Utterance
from dataclasses import dataclass
from kaia.eaglesong.amenities.partial_listen_translator import PartialListenTranslator


class ExpectedTemplatesListenPayload:
    def __init__(self, *expected_templates: Template|str):
        self.expected_templates = tuple(expected_templates)



class ExpectedTemplatesTranslator(PartialListenTranslator):
    def __init__(self, inner_function):
        super().__init__(inner_function, ExpectedTemplatesListenPayload, True)

    def captures_input(self, input):
        return isinstance(input, Utterance)

    def on_translate_input(self, payload: ExpectedTemplatesListenPayload, input):
        yield
        while True:
            for template in payload.expected_templates:
                if isinstance(template, Template):
                    if input in template:
                        return input
                if isinstance(template, str):
                    if input.template.name == template:
                        return input

            yield self.create_unexpected_message(input, payload.expected_templates)
            yield self.get_last_listen()


    def create_unexpected_message(self, utterance: Utterance, expected_templates: tuple[Template,...]):
        expected = []
        for template in expected_templates:
            if isinstance(template, str):
                expected.append(template)
            elif template.meta.as_input is not None and template.meta.as_input.caption is not None:
                expected.append(template.meta.as_input.caption)
            else:
                expected.append(template.name.split('.')[-1])
        return "Unexpected input. Expected: "+", ".join(expected)





