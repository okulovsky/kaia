from typing import *
from unittest import TestCase
from .structures import Dub
from .templates.template import Template, Utterance
from .templates import RhasspyHandler, RhasspyAPI
from .dubbing import Dubber
from dataclasses import dataclass
from copy import copy
from yo_fluq_ds import *

def check_dict(d1, d2):
    if not isinstance(d1, dict) or not isinstance(d2, dict):
        return False, False
    true_keys = tuple(sorted(d1))
    actual_keys = tuple(sorted(d2))
    if true_keys != actual_keys:
        return False, False

    for key in true_keys:
        if d1[key] != d2[key]:
            return True, False

    return True, True

@dataclass
class Sample:
    intent_obj: Template
    s: str
    true_intent: str
    true_value: Any

    recognition_obj: Any = None
    parsed_intent: Optional[str] = None
    parsed_value: Any = None
    failure: bool = False
    match_intent: bool = False
    match_keys: bool = False
    match_values: bool = False
    match: bool = False


    def set_matches(self):
        self.failure = self.parsed_intent is None
        if self.failure:
            self.match_keys = self.match_values = self.match_intent = self.match = False
        else:
            self.match_intent = self.true_intent == self.parsed_intent
            self.match_keys, self.match_values = check_dict(self.true_value, self.parsed_value)
            self.match = self.match_intent and self.match_keys and self.match_values

    def against_utterance(self, utterance: Optional[Utterance]):
        if utterance is not None:
            self.parsed_intent = utterance.template.name
            self.parsed_value = utterance.value
        else:
            self.parsed_intent = None
            self.parsed_value = None
        self.set_matches()

    def make_assert(self, case: TestCase):
        case.assertEqual(self.true_intent, self.parsed_intent)
        case.assertDictEqual(self.true_value, self.parsed_value)









class TestingTools:
    def __init__(self, intents: Union[Dub, Template, Iterable[Template]], random_count=100):
        if isinstance(intents, Dub):
            intents = [Template('{value}', value=intents).with_name('intent')]
        elif isinstance(intents, Template):
            intents = [intents.with_name('intent')]
        samples = []
        for intent in intents:
            seen_strings = set()
            for i in range(random_count):
                value = intent.get_random_value()
                strings = intent.to_all_strs(value)
                for s in strings:
                    if s in seen_strings:
                        continue
                    seen_strings.add(s)
                    samples.append(Sample(intent, s, intent.name, value))
        self.samples = samples
        self.intents = intents

    def parse_text(self, case: Optional[TestCase] = None):
        samples = copy(self.samples)
        for sample in samples:
            print(f'[PARSE] {sample.s}')
            sample.parsed_value = sample.intent_obj.parse(sample.s)
            sample.parsed_intent = sample.intent_obj.name
            if case is not None:
                sample.make_assert(case)
            sample.set_matches()
        return samples

    def parse_rhasspy(self, case: Optional[TestCase] = None):
        samples = copy(self.samples)
        handler = RhasspyHandler(self.intents)
        for sample in samples:
            print(f'[RHASSPY] {sample.s}')
            sample.against_utterance(handler.parse_string(sample.s))
            sample.recognition_obj = handler.recognitions_
            if case is not None:
                sample.make_assert(case)
        return samples


    def test_all_unit(self, case: TestCase):
        self.parse_text(case)
        self.parse_rhasspy(case)

    def test_voice(self, dubber: Dubber, api: RhasspyAPI):
        samples = copy(self.samples)
        for s in Query.en(samples).feed(fluq.with_progress_bar()):
            for i in range(5):
                try:
                    decomposition = dubber.decompose(s.s, s.intent_obj)
                    file = dubber.create_wav_file(decomposition)
                    utterance = api.recognize(file)
                    s.audio_file = file.name
                    s.recognition_obj = api.last_recognition_
                    s.decomposition = decomposition
                    s.against_utterance(utterance)
                    break
                except Exception as ex:
                    print(f'Timeout on {s.s}\n{ex}')
        return samples

    @staticmethod
    def samples_to_df(samples: Iterable[Sample]):
        df = pd.DataFrame([s.__dict__ for s in samples])
        df.true_value = df.true_value.apply(jsonpickle.dumps)
        df.parsed_value = df.parsed_value.apply(jsonpickle.dumps)
        df = df.drop('intent_obj', axis=1)
        return df







