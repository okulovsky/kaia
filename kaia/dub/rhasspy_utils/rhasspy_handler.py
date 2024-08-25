from typing import *
from ..core.algorithms import ToIni, IniRule
from ..core.templates import Template, Utterance
from . import rhasspy_nlu
from .functions import rule_to_section, rule_to_sample_str


class RhasspyHandler:
    def __init__(self, intents: Iterable[Template]):
        self.intent_to_template = {}
        self.intent_to_rules = {}
        self.intents = tuple(intents)
        for i, intent in enumerate(intents):
            if intent.name is None:
                raise ValueError(f"Intent at index {i} doesn't have a name, impossible to use in Rhasspy")

            self.intent_to_template[intent.name] = intent
            rule = ToIni().walk(intent.dub) #type: IniRule
            self.intent_to_rules[intent.name] = rule

        self.ini_file = '\n\n'.join(rule_to_section(rule, key) for key, rule in self.intent_to_rules.items())
        intents = rhasspy_nlu.parse_ini(self.ini_file)
        self.graph = rhasspy_nlu.intents_to_graph(intents)


    def _make_parse(self, intent_name, entities) -> Optional[Utterance]:
        if intent_name not in self.intent_to_template:
            return None
        # TODO: Actually, we can use a ValuesConvolutor here as well, but I'm afraid to touch it
        template = self.intent_to_template[intent_name]
        rule = self.intent_to_rules[intent_name]
        s = rule_to_sample_str(rule, entities)
        value = template.parse(s)
        return template.utter(value)

    def parse_json(self, recognition: Dict) -> Optional[Utterance]:
        intent_name = recognition['intent']['name']
        entities = {e['entity']:e['value'] for e in recognition['entities']}
        return self._make_parse(intent_name, entities)

    def parse_string(self, s: str):
        recognitions = rhasspy_nlu.recognize(rhasspy_nlu.escape_for_rhasspy(s), self.graph)
        self.recognitions_ = recognitions
        if len(recognitions)==0:
            return None
        rec = recognitions[0]
        entities = {e.entity:e.value for e in rec.entities}
        return self._make_parse(rec.intent.name, entities)



