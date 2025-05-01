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
            o = Ontology[MyModel]()
            prompt = o.prompt(f'Prompt for field_1={o.ref.field_1}')
            mapping = PromptMapping(
                PromptBasedObjectConverter(prompt, 'FakeText', '__call__', 'prefix'),
                'test',
                SimpleApplicator('field_2'),
            )

            with BrainBox.Api.Test() as api:
                result_1 = mapping.create(models,text_file).execute(api).result

                another_mapping = mapping.create(models+[MyModel(field_1='3')], text_file)

                task = another_mapping.build_collector_task()
                self.assertEqual(1, len(task.intermediate_tasks))
                another_mapping.apply_result(api.execute(task))
                result_2 = another_mapping.result

        self.assertEqual(
            [{'field_1': '1', 'field_2': 'Prompt for field_1=1'},
             {'field_1': '2', 'field_2': 'Prompt for field_1=2'},
             {'field_1': '3', 'field_2': 'Prompt for field_1=3'}],
            [r.__dict__ for r in result_2]
        )







