from chara.paraphrasing.common.grammar_correction.grammar_model import GrammarModel
from grammatron import Template, PluralAgreement, CardinalDub, DubParameters
from unittest import TestCase

class TestGrammarModel(TestCase):
    def test_grammar_model(self):
        t = Template(ru=f"Будильник заведен на {PluralAgreement(CardinalDub().as_variable('amount'),'минута')}")
        self.assertEqual(
            "Будильник заведен на одна минута",
            t.to_str(dict(amount=1))
        )
        g = GrammarModel.build(t)
        g.apply({
            "text": "...",
            "grammar": {
                "{amount+минута}" : {
                    "падеж": 'Винительный'
                }

            }
        })
        self.assertEqual(
            "Будильник заведен на одну минуту",
            t.to_str(dict(amount=1))
        )
        g.apply({
            "text": "...",
            "grammar": {
                "{amount+минута}" : {
                    "падеж": 'Творительный'
                }
            }
        })
        self.assertEqual(
            "Будильник заведен на одной минутой",
            t.to_str(dict(amount=1))
        )