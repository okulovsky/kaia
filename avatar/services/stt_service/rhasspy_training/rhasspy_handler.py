from typing import *
from grammatron import Template, Utterance
from .kaldi_grammar_builder import KaldiGrammarBuilder

class RhasspyHandler:
    def __init__(self, intents: Iterable[Template]):
        self.intent_to_template = {}
        self.intent_to_builder = {}
        self.intents = tuple(intents)

        for i, intent in enumerate(intents):
            if intent.get_name() is None:
                raise ValueError(f"Intent at index {i} doesn't have a name, impossible to use in Rhasspy")
            name = intent.get_name()
            self.intent_to_template[name] = intent
            try:
                builder = KaldiGrammarBuilder.make_all(intent.dub).build()
            except Exception as ex:
                raise ValueError(f"Template {i} with the name {intent.get_name()} raises exception when building Kaldi grammar") from ex
            self.intent_to_builder[name] = builder


        self.ini_file = '\n\n'.join(builder.to_rule(name) for name, builder in self.intent_to_builder.items())


    def parse_kaldi_output(self, kaldi_output: Dict) -> Optional[Utterance]:
        recognition = kaldi_output['fsticuffs']
        if len(recognition) == 0:
            return None
        recognition = recognition[0]
        intent_name = recognition['intent']['name']
        if intent_name not in self.intent_to_builder:
            return None
        builder = self.intent_to_builder[intent_name]
        value = builder.parse(recognition)
        return self.intent_to_template[intent_name].utter(value)

    def parse_string(self, s: str):
        for template in self.intent_to_template.values():
            try:
                return template.utter(template.parse(s))
            except:
                continue
        raise ValueError(f"String {s} cannot be recognized by any of the templates")
