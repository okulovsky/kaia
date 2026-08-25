import gc
import threading
import time
from unittest import TestCase

from foundation_kaia.misc.object_lock import ObjectLocks


class Dummy:
    pass


class ObjectLocksTestCase(TestCase):
    def test_same_object_gives_same_lock(self):
        locks = ObjectLocks()
        obj = Dummy()
        self.assertIs(locks.get(obj), locks.get(obj))

    def test_different_objects_give_different_locks(self):
        locks = ObjectLocks()
        self.assertIsNot(locks.get(Dummy()), locks.get(Dummy()))

    def test_lock_excludes_concurrent_access(self):
        locks = ObjectLocks()
        obj = Dummy()
        counter = {'value': 0, 'overlap': False, 'active': 0}

        def worker():
            with locks.lock(obj):
                counter['active'] += 1
                if counter['active'] > 1:
                    counter['overlap'] = True
                time.sleep(0.05)
                counter['value'] += 1
                counter['active'] -= 1

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(counter['value'], 5)
        self.assertFalse(counter['overlap'])

    def test_lock_is_reentrant(self):
        locks = ObjectLocks()
        obj = Dummy()
        with locks.lock(obj):
            with locks.lock(obj):
                pass

    def test_garbage_collected_object_does_not_leak_lock(self):
        locks = ObjectLocks()
        obj = Dummy()
        locks.get(obj)
        self.assertEqual(len(locks._locks), 1)
        del obj
        gc.collect()
        self.assertEqual(len(locks._locks), 0)

    def test_id_reuse_does_not_share_lock(self):
        # Regression test for the bug a plain `dict[id(obj), Lock]` would have:
        # once `first` is collected, a new object can be allocated at the same
        # address, so id(first) == id(second) is possible. The registry must
        # not treat them as the same key in that case.
        locks = ObjectLocks()
        first = Dummy()
        first_id = id(first)
        first_lock = locks.get(first)
        del first
        gc.collect()

        second = Dummy()
        if id(second) == first_id:
            self.assertIsNot(locks.get(second), first_lock)
