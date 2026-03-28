from datetime import timedelta
from unittest import TestCase
from grammatron import DubParameters
from grammatron.grammars.ru import RuGrammarRule, RuDeclension
from chara.paraphrasing.common import ParsedTemplate
from chara.paraphrasing.intents import CasePrompter, parse_case_response
from kaia.skills.timer_skill import TimerIntents


class CaseDetectionTestCase(TestCase):
    def test_case_prompter_contains_variable(self):
        paraphrase = "Поставь таймер на {duration}"
        prompt = CasePrompter()(paraphrase)
        self.assertIn('duration', prompt)

    def test_parse_case_response(self):
        cases = parse_case_response('{"duration": "accusative"}')
        self.assertEqual(RuDeclension.ACCUSATIVE, cases['duration'])

    def test_restore_and_substitute(self):
        paraphrase = "Поставь таймер на {duration}"

        mock_response = '{"duration": "instrumental"}'
        cases = parse_case_response(mock_response)

        template = next(t for t in TimerIntents.get_templates() if 'set_the_timer' in t.get_name())
        parsed = ParsedTemplate.parse(template)[0]
        restored = parsed.restore_template(paraphrase)

        result = restored.utter({'duration': timedelta(minutes=5)}).to_str(
            DubParameters(language='ru', grammar_rule=RuGrammarRule(cases['duration'])),
        )
        self.assertIn('минутами', result)
