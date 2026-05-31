from brainbox import BrainBox, File, ISelfManagingDecider
from chara.common import brainbox_pipeline, Chara
from unittest import TestCase
from foundation_kaia.misc import Loc


class MyMock(ISelfManagingDecider):
    def __init__(self):
        super().__init__()

    def produce(self, name: str):
        return File(name + '1', (name + '1').encode('ascii'))


class BrainBoxFilesTestCase(TestCase):
    def test_with_files(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([MyMock()]) as api:
                Chara.Apis.brainbox_api = api
                tasks = [BrainBox.TaskBuilder.call(MyMock).produce(s) for s in ['a', 'b']]
                Chara.call(brainbox_pipeline)(tasks, result_to_file=True)

            result = list(Chara.previous.result.read_all())
            self.assertEqual(2, len(result))
            for item in result:
                self.assertIsNone(item.error)
                self.assertTrue(item.result.is_file())
                expected_name = item.result.name
                self.assertEqual(expected_name.encode('ascii'), item.result.read_bytes())

    def test_keeps_file_in_cache_by_default(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([MyMock()]) as api:
                Chara.Apis.brainbox_api = api
                tasks = [BrainBox.TaskBuilder.call(MyMock).produce('cache_test')]
                Chara.call(brainbox_pipeline)(tasks, result_to_file=True)
                self.assertTrue(api.cache.is_file('cache_test1'))

    def test_removes_file_from_cache_when_enabled(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([MyMock()]) as api:
                Chara.Apis.brainbox_api = api
                tasks = [BrainBox.TaskBuilder.call(MyMock).produce('cache_test')]
                Chara.call(brainbox_pipeline)(tasks, result_to_file=True, remove_resulting_files_from_cache=True)
                self.assertFalse(api.cache.is_file('cache_test1'))
