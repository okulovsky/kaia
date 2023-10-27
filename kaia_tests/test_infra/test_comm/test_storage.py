import time
from unittest import TestCase
from kaia.infra.comm import Sql

class StorageTestCase(TestCase):
    def test_storage(self):
        for sql in [Sql.memory(), Sql.file()]:
            with self.subTest(type(sql).__name__):
                storage = sql.storage()
                for i in range(5):
                    storage.save('', i)
                self.assertListEqual([0, 1, 2, 3, 4], storage.load())
                self.assertListEqual([4,3,2,1,0], storage.load(historical_order=False))
                self.assertListEqual([2, 3, 4], storage.load(amount=3))
                self.assertListEqual([4,3,2], storage.load(amount=3, historical_order=False))
                self.assertListEqual([], storage.load(key='key'))
                for i in range(3):
                    storage.save('key', i)
                self.assertListEqual([0,1,2], storage.load(key='key'))


    def test_updates(self):
        storage = Sql.memory().storage()
        for i in range(5):
            storage.save('', i)
        updates = storage.load_update()
        self.assertListEqual(list(range(5)), [u.value for u in updates])
        time.sleep(0.1)
        for i in range(10,13):
            storage.save('', i)
        updates_1 = storage.load_update(last_update_id=updates[-1].id)
        self.assertListEqual(list(range(10, 13)), [u.value for u in updates_1])
        updates_2 = storage.load_update(last_update_timestamp=updates[-1].timestamp)
        self.assertListEqual(list(range(10, 13)), [u.value for u in updates_2])


