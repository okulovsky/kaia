from unittest import TestCase
from brainbox.framework import File, BrainBoxApi, FileIO, IDecider, FileLike, BrainBoxTask, Loc

class FileDecider(IDecider):
    def process(self, file: FileLike.Type):
        with FileLike(file, self.cache_folder) as data:
            return File('test-1.txt', data.read()+b'!')


class UploadsDownloadsTestCase(TestCase):
    def make_test(self, api: BrainBoxApi, custom_api_folder):
        if custom_api_folder is not None:
            api.cache_folder = custom_api_folder

        api.upload('test.txt', b'Hello')

        path = api.download('test.txt')

        if custom_api_folder is not None:
            self.assertEqual(custom_api_folder, path.parent)
        self.assertEqual(b'Hello', FileIO.read_bytes(path))

        file = api.open_file('test.txt')
        self.assertEqual(b'Hello', file.content)

        result = api.execute(BrainBoxTask.call(FileDecider).process('test.txt'))
        self.assertEqual('test-1.txt', result)

        self.assertEqual(b'Hello!', api.open_file('test-1.txt').content)


    def test_upload_and_download_in_different_folders(self):
        with Loc.create_test_folder() as api_folder:
            with BrainBoxApi.Test([FileDecider()]) as api:
                self.make_test(api, api_folder)

    def test_upload_and_download_in_same_folder(self):
        with BrainBoxApi.Test([FileDecider()]) as api:
            self.make_test(api, None)









