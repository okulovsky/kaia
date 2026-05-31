from brainbox import BrainBox, ISelfManagingDecider, File
from chara.common import brainbox_pipeline, Chara
from unittest import TestCase
from foundation_kaia.misc import Loc
from uuid import uuid4



class MyMock(ISelfManagingDecider):
    def __init__(self):
        super().__init__()

    def question(self, prompt: str):
        if prompt == 'error':
            raise ValueError()
        return f'result:'+prompt

    def one_file(self, prompt: str):
        if prompt == 'error':
            raise ValueError()
        return File(str(uuid4()), prompt.encode('utf-8'))

    def several_files(self, n: int):
        if n<0:
            raise ValueError()
        return [File(str(uuid4()), b'0'*i) for i in range(n)]



class BrainBoxPipelineTestCase(TestCase):
    def test_simple(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([MyMock()]) as api:
                Chara.Apis.brainbox_api = api
                tasks = [BrainBox.TaskBuilder.call(MyMock).question(t) for t in ['a', 'error', 'b']]
                Chara.call(brainbox_pipeline)(tasks)

            result = list(Chara.previous.result.read_all())
            self.assertEqual(3, len(result))
            self.assertIsNone(result[0].error)
            self.assertEqual('result:a', result[0].result)
            self.assertIsNone(result[2].error)
            self.assertEqual('result:b', result[2].result)
            self.assertIsNone(result[1].result)
            self.assertIsNotNone(result[1].error)

    def test_one_file(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([MyMock()]) as api:
                Chara.Apis.brainbox_api = api
                tasks = [BrainBox.TaskBuilder.call(MyMock).one_file(t) for t in ['a', 'error', 'b']]
                Chara.call(brainbox_pipeline)(tasks, result_to_file = True)

            result = list(Chara.previous.result.read_all())
            self.assertEqual(3, len(result))
            self.assertIsNone(result[0].error)
            self.assertEqual(b'a', result[0].result.read_bytes())
            self.assertIsNone(result[2].error)
            self.assertEqual(b'b', result[2].result.read_bytes())
            self.assertIsNone(result[1].result)
            self.assertIsNotNone(result[1].error)

    def test_several_files(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([MyMock()]) as api:
                Chara.Apis.brainbox_api = api
                tasks = [BrainBox.TaskBuilder.call(MyMock).several_files(t) for t in [2, -3, 1]]
                Chara.call(brainbox_pipeline)(tasks, result_to_file = lambda x: x)

            result = list(Chara.previous.result.read_all())
            self.assertEqual(3, len(result))
            self.assertIsNone(result[0].error)
            self.assertEqual(2, len(result[0].result))

            self.assertIsNone(result[2].error)
            self.assertEqual(1, len(result[2].result))

            self.assertIsNotNone(result[1].error)
            self.assertIsNone(result[1].result)

            for i in [0, 2]:
                for r in result[i].result:
                    self.assertTrue(r.is_file())







