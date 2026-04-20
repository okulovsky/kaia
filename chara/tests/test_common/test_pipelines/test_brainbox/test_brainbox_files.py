import shutil

from brainbox import BrainBox, File, ISelfManagingDecider
from brainbox.deciders import Collector
from chara.common import BrainBoxPipeline, BrainBoxCache, BrainBoxMerger, CharaApis
from unittest import TestCase
from foundation_kaia.misc import Loc
from pathlib import Path


class MyMock(ISelfManagingDecider):
    def __init__(self):
        super().__init__()

    def produce(self, name: str):
        return File(name+'1', (name+'1').encode('ascii'))


def create_task(s: str):
    return BrainBox.TaskBuilder.call(MyMock).produce(s)


class BrainBoxPipelineTestCase(TestCase):
    def test_with_files(self):
        with Loc.create_test_folder() as folder:
            #folder = (Path(__file__)).parent/'cache'; shutil.rmtree(folder, ignore_errors=True)

            cache = BrainBoxCache(folder)
            unit = BrainBoxPipeline(
                create_task,
                options_as_files=True
            )
            with BrainBox.Api.test([MyMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                unit.run(cache, ['a', 'b'])

            for option in cache.read_options():
                self.assertTrue(cache.get_file_path(option).is_file())
                file = cache.open_file(option)
                self.assertEqual(option.encode('ascii'), file.content)
                self.assertEqual(option, file.name)
