from kaia.brainbox.media_library import MediaLibrary
from kaia.brainbox import BrainBoxTestApi, BrainBoxTask, BrainBoxTaskPack, DownloadingPostprocessor
from unittest import TestCase
from kaia.brainbox.deciders.fake_dub_decider import FakeDubDecider
from kaia.brainbox.deciders.collector import Collector
from pathlib import Path

import zipfile
import pickle

def create_lib():
    deciders = dict(dub=FakeDubDecider(), collector=Collector())
    tasks = [BrainBoxTask(id=f'test_{i}', decider='dub', arguments=dict(text=f'test {i}', voice='test')) for i in
             range(10)]
    deps = {t.id: t.id for t in tasks}
    tags = {t.id: t.arguments for t in tasks}
    collection = BrainBoxTask(id='col', decider='collector', arguments=dict(tags=tags), dependencies=deps)
    pack = BrainBoxTaskPack(collection, tuple(tasks), DownloadingPostprocessor(opener=MediaLibrary.read))
    with BrainBoxTestApi(deciders) as api:
        lib = api.execute(pack)
    lib.save(Path(__file__).parent/'lib.zip')

class RawUnzippingTestCase(TestCase):
    def test_raw_unzipping(self):
        with zipfile.ZipFile(Path(__file__).parent/'lib.zip','r') as zip:
            records = pickle.loads(zip.read('description.pkl'))
            for value in records.values():
                self.assertIsInstance(value, dict)
        print(value)





