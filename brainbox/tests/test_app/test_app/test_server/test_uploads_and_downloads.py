from unittest import TestCase
from pathlib import Path
from brainbox.framework.common import ISelfManagingDecider
from brainbox.framework.brainbox import BrainBox
from brainbox.framework.app.api import BrainBoxApi
from foundation_kaia.marshalling_2 import File
from foundation_kaia.misc import Loc


class FileDecider(ISelfManagingDecider):
    def process(self, file: str):
        return File('test-1.txt', (self.cache_folder / file).read_bytes() + b'!')


class UploadsDownloadsTestCase(TestCase):

    def make_test(self, api: BrainBoxApi, download_folder: Path | None):
        api.cache.upload('test.txt', b'Hello')

        if download_folder is not None:
            path = api.cache.download('test.txt', download_folder)
            self.assertEqual(download_folder, path.parent)
        else:
            path = api.cache.download('test.txt', api.debug_locations.cache_folder)

        self.assertEqual(b'Hello', path.read_bytes())

        self.assertEqual(b'Hello', api.cache.read('test.txt'))

        result = api.execute(BrainBox.TaskBuilder.call(FileDecider).process('test.txt'))
        self.assertEqual('test-1.txt', result)

        self.assertEqual(b'Hello!', api.cache.read('test-1.txt'))

    def test_upload_and_download_in_different_folders(self):
        with Loc.create_test_folder() as download_folder:
            with BrainBoxApi.test([FileDecider()], port=18192) as api:
                self.make_test(api, download_folder)

    def test_upload_and_download_in_same_folder(self):
        with BrainBoxApi.test([FileDecider()], port=18192) as api:
            self.make_test(api, None)
