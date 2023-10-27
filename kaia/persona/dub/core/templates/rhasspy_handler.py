from typing import *
from ..algorithms import ToIni, IniRule, Parser
from .template import Template, Utterance
from ..utils import rhasspy_nlu


class RhasspyHandler:
    def __init__(self, intents: Iterable[Template]):
        self.intent_to_template = {}
        self.intent_to_rules = {}
        self.intents = tuple(intents)
        for intent in intents:
            self.intent_to_template[intent.name] = intent
            rule = ToIni().walk(intent.dub) #type: IniRule
            self.intent_to_rules[intent.name] = rule

        self.ini_file = '\n\n'.join(rule.generate_section(key) for key, rule in self.intent_to_rules.items())
        intents = rhasspy_nlu.parse_ini(self.ini_file)
        self.graph = rhasspy_nlu.intents_to_graph(intents)


    def _make_parse(self, intent_name, entities) -> Optional[Utterance]:
        if intent_name not in self.intent_to_template:
            return None
        template = self.intent_to_template[intent_name]
        rule = self.intent_to_rules[intent_name]
        s = rule.to_sample_str(entities)
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



