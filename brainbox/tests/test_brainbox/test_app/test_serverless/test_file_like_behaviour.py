from unittest import TestCase
from brainbox.framework import File, BrainBoxApi, BrainBoxTask, FileIO, IDecider, FileLike


class F(IDecider):
    def to_file(self, text: str):
        return File('test', text)

    def from_file(self, file: FileLike.Type):
        with FileLike(file, self.cache_folder) as stream:
            return stream.read().decode('utf-8')




class FileLikeTestCase(TestCase):
    def test_file_like(self):
        with BrainBoxApi.ServerlessTest([F()]) as api:
            S = 'Hello, test'
            file = api.execute(BrainBoxTask.call(F).to_file(text=S).to_task(id='test'))
            self.assertIsInstance(file, str)

            self.assertEqual(
                S, api.execute(BrainBoxTask.call(F).from_file(file=file))
            )

            self.assertEqual(
                S, api.execute(BrainBoxTask.call(F).from_file(file=api.cache_folder/file))
            )

            content = FileIO.read_bytes(api.cache_folder/file)
            self.assertEqual(
                S, api.execute(BrainBoxTask.call(F).from_file(file=content))
            )

