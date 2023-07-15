from unittest import TestCase
from kaia.infra import Sql
from kaia.bro.core import StorageClientDataProvider

class DataLoaderTestCase(TestCase):
    def test_loader(self):
        storage = Sql.memory().storage()
        r10 = list(range(10))
        for i in r10:
            storage.save('', i)
        loader = StorageClientDataProvider('', storage, 25)
        data = loader.pull()

        self.assertListEqual(r10, loader.data)
        self.assertListEqual(r10, data)

        r30 = list(range(30,40))
        for i in r30:
            storage.save('', i)
        data = loader.pull()
        self.assertListEqual(r10+r30, data)
        self.assertListEqual(r10 + r30, loader.data)

        r50 = list(range(50,60))
        for i in r50:
            storage.save('', i)

        data = loader.pull()
        self.assertListEqual(r10[5:]+r30+r50, data)
        self.assertListEqual(r10[5:]+r30+r50, loader.data)





