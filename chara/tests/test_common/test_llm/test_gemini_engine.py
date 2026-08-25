import base64
import sys
import time
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from brainbox.deciders import Ollama, Whisper

from chara.common.llm import LLMSetup

FOLDER = Path(__file__).parent


class _FakeClient:
    """Records what the engine sent and answers after `delay` seconds."""

    def __init__(self, delay: float = 0.0):
        self.delay = delay
        self.calls: list[dict] = []
        self.chat = MagicMock()
        self.chat.completions.create = self._create

    def _create(self, model, messages, **kwargs):
        self.calls.append(dict(model=model, messages=messages, **kwargs))
        content = messages[-1]['content']
        text = content if isinstance(content, str) else content[0]['text']
        if self.delay:
            time.sleep(self.delay)
        response = MagicMock()
        response.choices[0].message.content = f'answer to {text}'
        return response


class GeminiEngineTestCase(unittest.TestCase):
    """Covers the engine against a stubbed OpenAI client: no key, no network."""

    def setUp(self):
        self.client = _FakeClient()
        fake_openai = types.ModuleType('openai')
        fake_openai.OpenAI = lambda **kwargs: self.client
        patcher = patch.dict(sys.modules, {'openai': fake_openai})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _engine(self, **kwargs):
        from chara.common.llm import GeminiLLMEngine
        return GeminiLLMEngine(api_key='not-a-key', **kwargs)

    def _request(self, engine, builder=None):
        setup = LLMSetup(engine, 'gemini-test')
        builder = builder or (lambda b: b)
        return builder(setup.default().custom_prompt(lambda case: 'PROMPT')).to_request()

    def test_prompt_model_and_system_prompt_are_carried_over(self):
        request = self._request(self._engine(), lambda b: b.system_prompt('SYS'))
        self.assertEqual('answer to PROMPT', request.execute(None))
        call = self.client.calls[0]
        self.assertEqual('gemini-test', call['model'])
        self.assertEqual(
            [{'role': 'system', 'content': 'SYS'}, {'role': 'user', 'content': 'PROMPT'}],
            call['messages'],
        )

    def test_options_are_mapped_and_unsupported_ones_dropped(self):
        options = Ollama.Options(temperature=0.4, top_p=0.9, num_predict=64, top_k=5, mirostat=2, num_ctx=1024)
        request = self._request(self._engine(), lambda b: b.options(options))
        request.execute(None)
        call = self.client.calls[0]
        self.assertEqual(0.4, call['temperature'])
        self.assertEqual(0.9, call['top_p'])
        self.assertEqual(64, call['max_tokens'])
        self.assertEqual({'extra_body': {'google': {'top_k': 5}}}, call['extra_body'])
        self.assertNotIn('mirostat', call)
        self.assertNotIn('num_ctx', call)

    def test_json_schema_becomes_a_response_format(self):
        schema = {'type': 'object', 'properties': {}}
        request = self._request(self._engine(), lambda b: b.options(format=schema))
        request.execute(None)
        self.assertEqual(
            {'type': 'json_schema', 'json_schema': {'name': 'response', 'schema': schema, 'strict': True}},
            self.client.calls[0]['response_format'],
        )

    def test_image_is_inlined_as_base64(self):
        image = FOLDER/'case.jinja'
        request = self._request(self._engine(), lambda b: b.image(lambda case: image))
        request.execute(None)
        content = self.client.calls[0]['messages'][0]['content']
        self.assertEqual('PROMPT', content[0]['text'])
        expected = base64.b64encode(image.read_bytes()).decode('ascii')
        self.assertTrue(content[1]['image_url']['url'].endswith(expected))

    def test_start_does_not_block_and_calls_overlap(self):
        self.client.delay = 0.2
        setup = LLMSetup(self._engine(), 'gemini-test')
        request = setup.default().custom_prompt(lambda case: f'PROMPT {case}').to_request()

        started = time.monotonic()
        tokens = [request.start_execution(i) for i in range(4)]
        after_start = time.monotonic() - started
        results = [request.join_execution(i, token) for i, token in enumerate(tokens)]
        total = time.monotonic() - started

        self.assertLess(after_start, 0.1, "start_execution must not wait for the answer")
        self.assertLess(total, 0.6, "four 0.2s calls ran serially (0.8s+) instead of overlapping")
        self.assertEqual([f'answer to PROMPT {i}' for i in range(4)], results)

    def test_a_task_for_another_decider_is_rejected(self):
        engine = self._engine()
        with self.assertRaises(ValueError) as e:
            engine.start(Whisper.new_task().transcribe('recording.wav'))
        self.assertIn('Whisper', str(e.exception))

    def test_another_ollama_method_is_rejected(self):
        engine = self._engine()
        with self.assertRaises(ValueError) as e:
            engine.start(Ollama.new_task(parameter='m').completions('hi'))
        self.assertIn('completions', str(e.exception))


if __name__ == '__main__':
    unittest.main()
