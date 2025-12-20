from brainbox import BrainBox
from brainbox.deciders import Mock, Ollama
from unittest import TestCase

class MyMock(Mock):
    def __init__(self):
        super().__init__('Ollama')

    def question(self, prompt):
        return dict(prompt=prompt, method='question', parameter=self.parameter)

class MockDeciderTestCase(TestCase):
    def test_mock_decider(self):
        with BrainBox.Api.Test([MyMock()]) as api:
            result = api.execute(BrainBox.Task.call(Ollama,'test-model').question('test prompt'))
            self.assertDictEqual(
                {'method': 'question', 'parameter': 'test-model', 'prompt': 'test prompt'},
                result
            )
