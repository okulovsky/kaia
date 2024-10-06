from unittest import TestCase
from kaia.brainbox.core import IDecider, File, BrainBoxApi, BrainBoxTask
from kaia.brainbox.deciders.arch.utils import FileLike
from kaia.infra import Loc



class F(IDecider):
    def to_file(self, text: str):
        return File('test', text)

    def from_file(self, file: FileLike.Type):
        with FileLike(file, self.file_cache) as stream:
            return stream.read().decode('utf-8')

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass



class FileLikeTestCase(TestCase):
    def test_everything(self):
        with Loc.create_temp_folder('file_like_test_case') as folder:
            with BrainBoxApi.Test(dict(F=F()), folder) as api:
                S = 'Hello, test'
                file = api.execute(BrainBoxTask.call(F).to_file(text=S).to_task(id='test'))
                self.assertIsInstance(file, File)

                self.assertEqual(
                    S, api.execute(BrainBoxTask.call(F).from_file(file=file.name))
                )

                self.assertEqual(
                    S, api.execute(BrainBoxTask.call(F).from_file(file=folder/file.name))
                )

                self.assertEqual(
                    S, api.execute(BrainBoxTask.call(F).from_file(file=file))
                )

                api.pull_content(file)
                self.assertEqual(
                    S, api.execute(BrainBoxTask.call(F).from_file(file=file.content))
                )

                task = BrainBoxTask(
                    decider='F',
                    decider_method='from_file',
                    dependencies=dict(file='test')
                )
                self.assertEqual(
                    S, api.execute(task)
                )









