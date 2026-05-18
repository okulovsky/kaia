from brainbox import BrainBox, File, ISelfManagingDecider
from chara.common import Chara, BrainBoxCasePipeline, ICase, CaseCollection
from dataclasses import dataclass
from unittest import TestCase
from foundation_kaia.misc import Loc


@dataclass
class FileCase(ICase):
    name: str
    content: bytes
    result: str | None = None


def _case_to_file(case: FileCase) -> File:
    return File(case.name, case.content)


class CacheReadDecider(ISelfManagingDecider):
    def read(self, filename: str) -> str:
        return Chara.Apis.brainbox_api.cache.read(filename).decode('utf-8')


def _create_read_task(case: FileCase) -> BrainBox.Task:
    return BrainBox.TaskBuilder.call(CacheReadDecider).read(case.name)


class UploaderUnitTestCase(TestCase):
    def test_upload_puts_files_in_cache(self):
        uploader = BrainBoxCasePipeline.Uploader(_case_to_file)
        cases = [FileCase('a.bin', b'hello'), FileCase('b.bin', b'world')]
        with BrainBox.Api.serverless_test([]) as api:
            Chara.Apis.brainbox_api = api
            names = uploader.upload(cases)
            self.assertEqual({'a.bin', 'b.bin'}, names)
            self.assertEqual(b'hello', api.cache.read('a.bin'))
            self.assertEqual(b'world', api.cache.read('b.bin'))

    def test_cleanup_removes_files_when_remove_after_true(self):
        uploader = BrainBoxCasePipeline.Uploader(_case_to_file, remove_after=True)
        cases = [FileCase('c.bin', b'data')]
        with BrainBox.Api.serverless_test([]) as api:
            Chara.Apis.brainbox_api = api
            names = uploader.upload(cases)
            self.assertTrue(api.cache.is_file('c.bin'))
            uploader.cleanup(names)
            self.assertFalse(api.cache.is_file('c.bin'))

    def test_cleanup_keeps_files_when_remove_after_false(self):
        uploader = BrainBoxCasePipeline.Uploader(_case_to_file, remove_after=False)
        cases = [FileCase('d.bin', b'data')]
        with BrainBox.Api.serverless_test([]) as api:
            Chara.Apis.brainbox_api = api
            names = uploader.upload(cases)
            uploader.cleanup(names)
            self.assertTrue(api.cache.is_file('d.bin'))

    def test_deduplication_uploads_once_first_content_wins(self):
        uploader = BrainBoxCasePipeline.Uploader(_case_to_file)
        cases = [FileCase('shared.bin', b'first'), FileCase('shared.bin', b'second')]
        with BrainBox.Api.serverless_test([]) as api:
            Chara.Apis.brainbox_api = api
            names = uploader.upload(cases)
            self.assertEqual({'shared.bin'}, names)
            self.assertEqual(b'first', api.cache.read('shared.bin'))

    def test_multiple_files_per_case(self):
        def multi_file(case: FileCase):
            return [File(f'{case.name}_1.bin', b'part1'), File(f'{case.name}_2.bin', b'part2')]

        uploader = BrainBoxCasePipeline.Uploader(multi_file)
        cases = [FileCase('x', b'')]
        with BrainBox.Api.serverless_test([]) as api:
            Chara.Apis.brainbox_api = api
            names = uploader.upload(cases)
            self.assertEqual({'x_1.bin', 'x_2.bin'}, names)
            self.assertTrue(api.cache.is_file('x_1.bin'))
            self.assertTrue(api.cache.is_file('x_2.bin'))


class UploaderIntegrationTestCase(TestCase):
    def test_pipeline_reads_uploaded_files_and_cleans_up(self):
        uploader = BrainBoxCasePipeline.Uploader(_case_to_file, remove_after=True)
        unit = BrainBoxCasePipeline(_create_read_task, 'result', uploader=uploader)
        cases = [FileCase('upload_a.bin', b'content_a'), FileCase('upload_b.bin', b'content_b')]

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test([CacheReadDecider()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(unit.__call__)(CaseCollection(cases))
                self.assertFalse(api.cache.is_file('upload_a.bin'))
                self.assertFalse(api.cache.is_file('upload_b.bin'))

        all_cases = result.cases
        self.assertEqual(2, len(all_cases))
        case_a = next(c for c in all_cases if c.name == 'upload_a.bin')
        self.assertIsNone(case_a.error)
        self.assertEqual('content_a', case_a.result)
        case_b = next(c for c in all_cases if c.name == 'upload_b.bin')
        self.assertIsNone(case_b.error)
        self.assertEqual('content_b', case_b.result)
