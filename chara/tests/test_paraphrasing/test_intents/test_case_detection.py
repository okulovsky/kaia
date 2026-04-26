from datetime import timedelta
from unittest import TestCase
from grammatron import DubParameters
from grammatron.grammars.ru import RuCase
from chara.paraphrasing.common import ParsedTemplate
from chara.paraphrasing.intents import GrammarPrompter, RuGrammarPrompter
from kaia.skills.timer_skill import TimerIntents



class CaseDetectionTestCase(TestCase):
    def test_case_prompter_contains_variable(self):
        paraphrase = "Поставь таймер на {duration}"
        prompt = GrammarPrompter()(paraphrase)
        self.assertIn('duration', prompt)

    def test_parse_case_response(self):
        cases = RuGrammarPrompter().parse_case_response('{"duration": "accusative"}')
        self.assertEqual(RuCase.ACCUSATIVE, cases['duration'].declension)

    def test_restore_and_substitute(self):
        paraphrase = "Поставь таймер на {duration}"
        grammar_rules = RuGrammarPrompter().parse_case_response('{"duration": "instrumental"}')
        template = next(t for t in TimerIntents.get_templates() if 'set_the_timer' in t.get_name())
        parsed = ParsedTemplate.parse(template)[0]
        restored = parsed.restore_template(paraphrase, grammar_rules)
        result = restored.utter({'duration': timedelta(minutes=5)}).to_str(DubParameters(language='ru'))
        self.assertIn('минутами', result)
