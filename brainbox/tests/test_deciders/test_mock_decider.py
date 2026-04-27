from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Ollama
from unittest import TestCase

class MyMock(ISelfManagingDecider):
    def warmup(self, parameter: str|None):
        self.parameter = parameter

    def question(self, prompt):
        return dict(prompt=prompt, method='question', parameter=self.parameter)

    def get_name(self):
        return "Ollama"

class MockDeciderTestCase(TestCase):
    def test_mock_decider(self):
        with BrainBox.Api.test([MyMock()]) as api:
            result = api.execute(Ollama.new_task(parameter='test-model').question('test prompt'))
            self.assertDictEqual(
                {'method': 'question', 'parameter': 'test-model', 'prompt': 'test prompt'},
                result
            )
