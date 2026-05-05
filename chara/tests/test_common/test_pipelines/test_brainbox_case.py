from brainbox import ISelfManagingDecider, BrainBox, File
from chara.common import Chara, BrainBoxCasePipeline, ICase, CaseCollection
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
        return File('filename_' + prompt, ('content ' + prompt).encode('utf-8'))


@dataclass
class Case(ICase):
    prompt: str
    result: str | None = None


def create_task(case: Case) -> BrainBox.Task:
    return BrainBox.TaskBuilder.call(MyMock).question(case.prompt)


def create_file_task(case: Case) -> BrainBox.Task:
    return BrainBox.TaskBuilder.call(MyMock).file(case.prompt)


def apply(case: Case, reply: str):
    case.result = reply


class BrainboxCaseTestCase(TestCase):
    def test_simple(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            unit = BrainBoxCasePipeline(create_task, apply)
            with BrainBox.Api.serverless_test([MyMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(unit.__call__)(CaseCollection([Case('success'), Case('error')]))

        all_cases = result.cases
        self.assertEqual(2, len(all_cases))
        success = next(c for c in all_cases if c.prompt == 'success')
        self.assertEqual('reply 1: success\nreply 2: success', success.result)
        error = next(c for c in all_cases if c.prompt == 'error')
        self.assertIsNotNone(error.error)

    def test_with_divider(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            unit = BrainBoxCasePipeline(create_task, apply, lambda s: s.split('\n'))
            with BrainBox.Api.serverless_test([MyMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(unit.__call__)(CaseCollection([Case('success'), Case('error')]))

        all_cases = result.cases
        self.assertEqual(3, len(all_cases))
        errors = [c for c in all_cases if c.prompt == 'error']
        self.assertEqual(1, len(errors))
        self.assertIsNotNone(errors[0].error)

    def test_file(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            unit = BrainBoxCasePipeline(create_file_task, apply, result_to_file=True)
            with BrainBox.Api.serverless_test([MyMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(unit)(CaseCollection([Case('success'), Case('error')]))

            all_cases = result.cases
            success = next(c for c in all_cases if c.prompt == 'success')
            self.assertIsNone(success.error)
            self.assertTrue(success.result.is_file())
            error = next(c for c in all_cases if c.prompt == 'error')
            self.assertIsNotNone(error.error)
