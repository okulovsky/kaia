from unittest import TestCase
from dataclasses import dataclass
from brainbox.flow import Referrer, Prompter, SimpleApplicator, PromptBasedObjectConverter, BrainBoxMappingStep, BrainBoxMapping
from brainbox import BrainBox
from kaia.common import Loc

@dataclass
class MyModel:
    field_1: str
    field_2: str|None = None

class PromptMappingTestCase(TestCase):
    def test_simple(self):
        models = [MyModel(field_1='1'), MyModel(field_1='2')]
        o = Referrer[MyModel]()
        prompt = Prompter(f'Prompt for field_1={o.ref.field_1}')

        with BrainBox.Api.Test() as api:
            mapping = BrainBoxMappingStep(
                api,
                BrainBoxMapping(
                    PromptBasedObjectConverter(
                        prompt,
                        '',
                        decider_name='FakeText',
                        decider_method='__call__',
                        prompt_argument_name='prefix'
                    ),
                    SimpleApplicator('field_2'),
                )
            )
            result = mapping.process([], models).result

        print(result)
        self.assertEqual(
            [{'field_1': '1', 'field_2': 'Prompt for field_1=1'},
             {'field_1': '2', 'field_2': 'Prompt for field_1=2'}],
            [r.__dict__ for r in result]
        )

    def test_cache(self):
        models = [MyModel(field_1='1'), MyModel(field_1='2')]
        with Loc.create_test_file() as text_file:
            o = Referrer[MyModel]()
            prompt = Prompter(f'Prompt for field_1={o.ref.field_1}')

            with BrainBox.Api.Test() as api:
                mapping = BrainBoxMappingStep(
                    api,
                    BrainBoxMapping(
                        PromptBasedObjectConverter(
                            prompt,
                            '',
                            decider_name='FakeText',
                            decider_method='__call__',
                            prompt_argument_name='prefix'
                        ),
                        SimpleApplicator('field_2'),
                    ),
                    text_file
                )
                result_1 = mapping.process([], models).result

                result_2 = mapping.process([], models+[MyModel(field_1='3')])
                self.assertEqual(2, sum(result_2.is_task_cached))

        self.assertEqual(
            [{'field_1': '1', 'field_2': 'Prompt for field_1=1'},
             {'field_1': '2', 'field_2': 'Prompt for field_1=2'},
             {'field_1': '3', 'field_2': 'Prompt for field_1=3'}],
            [r.__dict__ for r in result_2.result]
        )







