from brainbox import ISelfManagingDecider, BrainBox, File
from brainbox.deciders import Ollama, Collector
from chara.common.pipelines.cases import ICase, BrainBoxCasePipeline, CaseCache
from chara.common import CharaApis
from dataclasses import dataclass
from unittest import TestCase
from foundation_kaia.misc import Loc


class MyMock(ISelfManagingDecider):
    def question(self, prompt: str) -> str:
        if prompt.startswith("error"):
            raise ValueError(prompt)
        return "reply 1: " + prompt + "\nreply 2: " + prompt

    def file(self, prompt: str):
        if prompt.startswith("error"):
            raise ValueError(prompt)
        return File('filename_'+prompt, ('content '+prompt).encode('utf-8'))

@dataclass
class Case(ICase):
    prompt: str
    result: str|None = None

def create_task(case: Case) -> BrainBox.Task:
    return BrainBox.TaskBuilder.call(MyMock).question(case.prompt)

def create_file_task(case: Case) -> BrainBox.Task:
    return BrainBox.TaskBuilder.call(MyMock).file(case.prompt)

def apply(case: Case, reply: str):
    case.result = reply

class BrainboxCaseTestCase(TestCase):
    def test_simple(self):
        with Loc.create_test_folder() as folder:
            cache = CaseCache[Case](folder)
            unit = BrainBoxCasePipeline(
                create_task,
                apply
            )
            with BrainBox.Api.serverless_test([MyMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                unit(cache, [Case('success'), Case('error')])
                result = cache.read_result()
            self.assertEqual(2, len(result))
            success = next(c for c in result if c.prompt=='success')
            self.assertEqual('reply 1: success\nreply 2: success', success.result)
            error = next(c for c in result if c.prompt=='error')
            self.assertIsNotNone(error.error)


    def test_with_divider(self):
        with Loc.create_test_folder() as folder:
            cache = CaseCache[Case](folder)
            unit = BrainBoxCasePipeline(
                create_task,
                apply,
                lambda s: s.split('\n')
            )
            with BrainBox.Api.serverless_test([MyMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                unit(cache, [Case('success'), Case('error')])
                result = cache.read_result()
            self.assertEqual(2, len(result))
            print(result)

    def test_file(self):
        with Loc.create_test_folder() as folder:
            cache = CaseCache[Case](folder)
            unit = BrainBoxCasePipeline(
                create_file_task,
                apply,
                options_as_files=True
            )
            with BrainBox.Api.serverless_test([MyMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                unit(cache, [Case('success'), Case('error')])
                result = cache.read_result()
            print(result)
