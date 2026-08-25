import io
import unittest
from contextlib import redirect_stdout
from dataclasses import dataclass
from pathlib import Path

from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Ollama
from foundation_kaia.marshalling import FileLike

from chara.common import Chara
from chara.common.llm import BrainBoxLLMEngine, LLMSetup

FOLDER = Path(__file__).parent


class OllamaMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str|None = None, options: Ollama.Options|None = None, image: FileLike|None = None) -> str:
        return f'{prompt}|{system_prompt}'


@dataclass
class Case:
    name: str = 'Alice'


class BrainBoxLLMEngineTestCase(unittest.TestCase):
    """The only tests that exercise BrainBoxLLMEngine itself.

    A pipeline never touches the engine — BrainBoxCasePipeline talks to the api
    directly — so start/join are only reached through execute().
    """

    def setUp(self):
        self.previous_api = Chara.Apis.brainbox_api
        self.api_context = BrainBox.Api.serverless_test([OllamaMock()])
        Chara.Apis.brainbox_api = self.api_context.__enter__()

    def tearDown(self):
        Chara.Apis.brainbox_api = self.previous_api
        self.api_context.__exit__(None, None, None)

    def _request(self, engine: BrainBoxLLMEngine):
        return (LLMSetup(engine, 'test-model')
                .default()
                .template(FOLDER/'case.jinja')
                .parse(lambda case, output: output.strip())
                .to_request())

    def test_execute_round_trip(self):
        request = self._request(BrainBoxLLMEngine())
        self.assertEqual('Hello, Alice!|None', request.execute(Case()))

    def test_system_prompt_reaches_the_decider(self):
        request = self._request(BrainBoxLLMEngine()).edit().system_prompt('SYS').to_request()
        self.assertEqual('Hello, Alice!|SYS', request.execute(Case()))

    def test_start_returns_a_token_and_join_resolves_it(self):
        engine = BrainBoxLLMEngine()
        request = self._request(engine)
        first = request.start_execution(Case('Alice'))
        second = request.start_execution(Case('Bob'))
        self.assertNotEqual(first, second)
        # Joined out of order: the token identifies the job, not the call order.
        self.assertEqual('Hello, Bob!|None', request.join_execution(Case('Bob'), second))
        self.assertEqual('Hello, Alice!|None', request.join_execution(Case('Alice'), first))

    def test_engine_reads_the_api_lazily(self):
        # The engine is built before the api exists, which is what every factory does.
        engine = BrainBoxLLMEngine()
        self.assertIs(Chara.Apis.brainbox_api, engine.api)

    def test_debug_prints_model_prompt_and_answer(self):
        setup = LLMSetup(BrainBoxLLMEngine(), 'test-model').debug()
        request = setup.default().template(FOLDER/'case.jinja').to_request()
        output = io.StringIO()
        with redirect_stdout(output):
            request.execute(Case())
        printed = output.getvalue()
        self.assertIn('test-model', printed)
        self.assertIn('Hello, Alice!', printed)

    def test_debug_is_off_by_default(self):
        request = self._request(BrainBoxLLMEngine())
        output = io.StringIO()
        with redirect_stdout(output):
            request.execute(Case())
        self.assertEqual('', output.getvalue())


if __name__ == '__main__':
    unittest.main()
