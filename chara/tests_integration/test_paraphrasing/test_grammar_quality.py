from chara.common import CharaApis
from chara.common.tools.llm import PromptTaskBuilder
from grammatron import OptionsDub, Template, PluralAgreement, CardinalDub
from grammatron.grammars.ru import RuCase
from unittest import TestCase
from dataclasses import dataclass
from chara.paraphrasing.grammar_correction import GrammarModel, GrammarCorrectionPipeline, GrammarCorrectionCache
from typing import Any
from foundation_kaia.misc import Loc
from brainbox import BrainBox


option = OptionsDub(['банан', 'яблоко', 'груша']).as_variable('fruit')
time = PluralAgreement(CardinalDub().as_variable('amount'), "час")

dataset = {
    f'Я хочу {option}' : RuCase.ACCUSATIVE,
    f'У меня нет {option}' : RuCase.GENITIVE,
    f"Мне нужна сахарная пудра к {option}": RuCase.DATIVE,
    f'На столе лежит {option}': RuCase.NOMINATIVE,
    f'Я позавтракал {option}': RuCase.INSTRUMENTAL,
    f'Я думаю о {option}': RuCase.PREPOSITIONAL,
    f"Я приду около {time}": RuCase.GENITIVE,
    f"Мне нужно {time}, чтобы сделать это": RuCase.ACCUSATIVE,
    f"Я приду к {time}": RuCase.DATIVE
}

@dataclass
class ParaphraseCase:
    template: Template
    expected_case: RuCase
    language: str
    grammar_model: GrammarModel|None = None
    grammar_reply: Any|None = None


class GrammarCorrectiomPipelineTestCase(TestCase):
    def test_grammar_correction_pipeline(self):
        cases = []
        for s, v in dataset.items():
            for i in range(10):
                cases.append(ParaphraseCase(
                    Template(ru=s),
                    v,
                    'ru'
                ))
        with Loc.create_test_folder() as folder:
            with BrainBox.Api.test() as api:
                CharaApis.brainbox_api = api
                cache = GrammarCorrectionCache[ParaphraseCase](folder)
                pipe = GrammarCorrectionPipeline[ParaphraseCase](
                    PromptTaskBuilder('mistral-small'),
                )
                pipe(cache, cases)

            for c in cache.read_result():
                print(c.expected_case)
                print(c.grammar_reply)
                print("\n")
