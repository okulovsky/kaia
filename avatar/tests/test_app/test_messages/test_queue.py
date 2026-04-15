import threading
from datetime import datetime
from time import sleep
from unittest import TestCase

from avatar.app.messages import *
from avatar.messaging.core import Envelop


def make_msg(id: str) -> AvatarMessage:
    return AvatarMessage(session='sess', content_type='type_a', envelop=Envelop(id=id), content={})


def make_msg_ts(id: str, ts: datetime) -> AvatarMessage:
    return AvatarMessage(session='sess', content_type='type_a', envelop=Envelop(id=id, timestamp=ts), content={})


class TestQueue(TestCase):

    def test_empty_queue_has_zero_len(self):
        q = Queue(60)
        self.assertEqual(0, len(q))

    def test_add_increments_len(self):
        q = Queue(60)
        q.add(make_msg('1'))
        q.add(make_msg('2'))
        self.assertEqual(2, len(q))

    def test_getitem_returns_correct_message(self):
        q = Queue(60)
        m0 = make_msg('0')
        m1 = make_msg('1')
        q.add(m0)
        q.add(m1)
        self.assertIs(m0, q[0])
        self.assertIs(m1, q[1])

    def test_get_index_returns_absolute_index(self):
        q = Queue(60)
        q.add(make_msg('a'))
        q.add(make_msg('b'))
        q.add(make_msg('c'))
        self.assertEqual(0, q.get_index('a'))
        self.assertEqual(1, q.get_index('b'))
        self.assertEqual(2, q.get_index('c'))

    def test_get_index_returns_none_for_unknown_id(self):
        q = Queue(60)
        q.add(make_msg('a'))
        self.assertIsNone(q.get_index('x'))

    def test_first_index_starts_at_zero(self):
        q = Queue(60)
        q.add(make_msg('a'))
        self.assertEqual(0, q.first_index)

    def test_ttl_removes_expired_messages(self):
        q = Queue(0.05)
        q.add(make_msg('old'))
        sleep(0.1)
        q.add(make_msg('new'))   # triggers cleanup
        # len() returns absolute upper bound; accessible count = len - first_index
        self.assertEqual(1, len(q) - q.first_index)
        self.assertIsNone(q.get_index('old'))

    def test_first_index_advances_after_ttl(self):
        q = Queue(0.05)
        q.add(make_msg('a'))
        q.add(make_msg('b'))
        self.assertEqual(0, q.first_index)
        sleep(0.1)
        q.add(make_msg('c'))     # removes 'a' and 'b'
        self.assertEqual(2, q.first_index)

    def test_getitem_uses_absolute_index_after_ttl(self):
        """After TTL removes 2 items, the new message is accessible at absolute index 2."""
        q = Queue(0.05)
        q.add(make_msg('a'))
        q.add(make_msg('b'))
        sleep(0.1)
        m = make_msg('c')
        q.add(m)
        self.assertIs(m, q[2])

    def test_get_index_stable_after_ttl(self):
        """get_index on a surviving message must equal first_index after earlier items expire."""
        q = Queue(0.05)
        q.add(make_msg('a'))
        q.add(make_msg('b'))
        sleep(0.1)
        m = make_msg('c')
        q.add(m)
        idx = q.get_index('c')
        self.assertEqual(q.first_index, idx)
        self.assertIs(m, q[idx])

    def test_expired_id_not_found_after_ttl(self):
        q = Queue(0.05)
        q.add(make_msg('old'))
        sleep(0.1)
        q.add(make_msg('new'))
        self.assertIsNone(q.get_index('old'))
        self.assertIsNotNone(q.get_index('new'))

    # --- find_index_from_timestamp ---

    def test_find_index_from_timestamp_returns_first_message_at_or_after(self):
        t1 = datetime(2024, 1, 1, 0, 0, 1)
        t2 = datetime(2024, 1, 1, 0, 0, 2)
        t3 = datetime(2024, 1, 1, 0, 0, 3)
        q = Queue(None)
        q.add(make_msg_ts('a', t1))
        q.add(make_msg_ts('b', t2))
        q.add(make_msg_ts('c', t3))
        t_query = datetime(2024, 1, 1, 0, 0, 2)
        self.assertEqual(1, q.find_index_from_timestamp(t_query))

    def test_find_index_from_timestamp_before_all_returns_first_index(self):
        t1 = datetime(2024, 1, 1, 0, 0, 1)
        q = Queue(None)
        q.add(make_msg_ts('a', t1))
        q.add(make_msg_ts('b', datetime(2024, 1, 1, 0, 0, 2)))
        self.assertEqual(0, q.find_index_from_timestamp(datetime(2024, 1, 1, 0, 0, 0)))

    def test_find_index_from_timestamp_after_all_returns_past_end(self):
        t1 = datetime(2024, 1, 1, 0, 0, 1)
        q = Queue(None)
        q.add(make_msg_ts('a', t1))
        q.add(make_msg_ts('b', datetime(2024, 1, 1, 0, 0, 2)))
        self.assertEqual(2, q.find_index_from_timestamp(datetime(2024, 1, 1, 0, 0, 9)))

    def test_find_index_from_timestamp_empty_queue_returns_zero(self):
        q = Queue(None)
        self.assertEqual(0, q.find_index_from_timestamp(datetime(2024, 1, 1)))

    def test_find_index_from_timestamp_stable_after_ttl(self):
        """After TTL removes early messages, the index reflects the surviving window."""
        t1 = datetime(2024, 1, 1, 0, 0, 1)
        t2 = datetime(2024, 1, 1, 0, 0, 2)
        t3 = datetime(2024, 1, 1, 0, 0, 3)
        q = Queue(None)
        q.add(make_msg_ts('a', t1))
        q.add(make_msg_ts('b', t2))
        # manually expire 'a' by bumping offset
        q._messages.pop(0)
        q._offset += 1
        q.add(make_msg_ts('c', t3))
        # 'b' is at absolute index 1, 'c' at 2
        self.assertEqual(1, q.find_index_from_timestamp(t2))
        self.assertEqual(2, q.find_index_from_timestamp(t3))

    def test_concurrent_adds_do_not_corrupt_length(self):
        q = Queue(60)
        n = 200
        threads = [threading.Thread(target=lambda i=i: q.add(make_msg(str(i)))) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(n, len(q))
