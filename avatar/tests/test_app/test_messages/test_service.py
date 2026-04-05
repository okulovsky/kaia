import threading
from datetime import datetime
from time import sleep
from unittest import TestCase
from dataclasses import dataclass

from avatar.app.messages import *
from avatar.messaging import IMessage, Envelop
from foundation_kaia.marshalling_2 import TypeTools


def make_msg(id: str, session: str = 'sess', content_type: str = 'type_a') -> AvatarMessage:
    return AvatarMessage(session=session, content_type=content_type, envelop=Envelop(id=id), content={})


@dataclass
class MsgA(IMessage):
    value: str = ''


@dataclass
class MsgB(IMessage):
    value: str = ''


class TestAvatarMessagingService(TestCase):

    def setUp(self):
        self.svc = AvatarMessagingService()

    def _put(self, id: str, session: str = 'sess', content_type: str = 'type_a'):
        self.svc.put(make_msg(id, session, content_type))

    # --- unknown session ---

    def test_get_unknown_session_returns_missing_session(self):
        result = self.svc.get('ghost', timeout_in_seconds=0)
        self.assertTrue(result.missing_session)
        self.assertEqual([], result.messages)

    def test_get_unknown_session_missing_id_reflects_whether_last_id_was_given(self):
        r_no_id = self.svc.get('ghost', timeout_in_seconds=0)
        r_with_id = self.svc.get('ghost', last_id='x', timeout_in_seconds=0)
        self.assertFalse(r_no_id.missing_id)
        self.assertTrue(r_with_id.missing_id)

    def test_tail_unknown_session_returns_missing_session(self):
        result = self.svc.tail('ghost', 5)
        self.assertTrue(result.missing_session)

    # --- basic get ---

    def test_get_all_messages_when_no_last_id(self):
        for i in range(3):
            self._put(str(i))
        result = self.svc.get('sess', timeout_in_seconds=0)
        self.assertEqual(3, len(result.messages))
        self.assertFalse(result.missing_id)
        self.assertFalse(result.missing_session)

    def test_get_returns_messages_after_last_id(self):
        for i in range(5):
            self._put(str(i))
        result = self.svc.get('sess', last_id='1', timeout_in_seconds=0)
        self.assertEqual(['2', '3', '4'], [m.envelop.id for m in result.messages])

    def test_get_last_id_at_end_returns_empty_on_timeout(self):
        for i in range(3):
            self._put(str(i))
        result = self.svc.get('sess', last_id='2', timeout_in_seconds=0.05)
        self.assertEqual([], result.messages)

    def test_get_unknown_last_id_sets_missing_id_and_returns_from_start(self):
        for i in range(3):
            self._put(str(i))
        result = self.svc.get('sess', last_id='no_such', timeout_in_seconds=0)
        self.assertTrue(result.missing_id)
        self.assertEqual(3, len(result.messages))

    def test_get_no_last_id_missing_id_is_false(self):
        self._put('0')
        result = self.svc.get('sess', timeout_in_seconds=0)
        self.assertFalse(result.missing_id)

    # --- max_messages ---

    def test_get_max_messages_limits_result(self):
        for i in range(5):
            self._put(str(i))
        result = self.svc.get('sess', max_messages=2, timeout_in_seconds=0)
        self.assertEqual(['0', '1'], [m.envelop.id for m in result.messages])

    def test_get_max_messages_larger_than_queue_returns_all(self):
        for i in range(3):
            self._put(str(i))
        result = self.svc.get('sess', max_messages=100, timeout_in_seconds=0)
        self.assertEqual(3, len(result.messages))

    # --- allowed_types ---

    def test_get_allowed_types_filters_results(self):
        for i in range(3):
            self._put(str(i), content_type='type_a')
            self._put(f'b{i}', content_type='type_b')
        result = self.svc.get('sess', allowed_types=['type_a'], timeout_in_seconds=0)
        self.assertEqual(3, len(result.messages))
        self.assertTrue(all(m.content_type == 'type_a' for m in result.messages))

    def test_get_allowed_types_no_match_returns_empty_on_timeout(self):
        self._put('0', content_type='type_a')
        result = self.svc.get('sess', allowed_types=['type_b'], timeout_in_seconds=0.05)
        self.assertEqual([], result.messages)

    def test_get_allowed_types_skips_non_matching_and_waits_for_matching(self):
        self._put('0', content_type='type_a')
        result_holder = []

        def reader():
            r = self.svc.get('sess', last_id='0', allowed_types=['type_b'], timeout_in_seconds=2)
            result_holder.append(r)

        t = threading.Thread(target=reader)
        t.start()
        sleep(0.05)
        self._put('1', content_type='type_a')   # should be skipped
        sleep(0.05)
        self._put('2', content_type='type_b')   # should unblock
        t.join(timeout=2)

        self.assertEqual(1, len(result_holder[0].messages))
        self.assertEqual('2', result_holder[0].messages[0].envelop.id)

    # --- blocking get ---

    def test_get_blocks_until_message_arrives(self):
        self._put('0')
        result_holder = []

        def reader():
            r = self.svc.get('sess', last_id='0', timeout_in_seconds=2)
            result_holder.append(r)

        t = threading.Thread(target=reader)
        t.start()
        sleep(0.05)
        self._put('1')
        t.join(timeout=2)

        self.assertEqual(1, len(result_holder))
        self.assertEqual('1', result_holder[0].messages[0].envelop.id)

    # --- tail ---

    def test_tail_returns_last_n(self):
        for i in range(5):
            self._put(str(i))
        result = self.svc.tail('sess', 3)
        self.assertEqual(['2', '3', '4'], [m.envelop.id for m in result.messages])

    def test_tail_count_larger_than_queue_returns_all(self):
        for i in range(2):
            self._put(str(i))
        result = self.svc.tail('sess', 10)
        self.assertEqual(2, len(result.messages))

    def test_tail_allowed_types_filters_before_counting(self):
        # type_a: 0, 2, 4  |  type_b: 1, 3
        for i in range(5):
            self._put(str(i), content_type='type_a' if i % 2 == 0 else 'type_b')
        result = self.svc.tail('sess', 2, allowed_types=['type_a'])
        self.assertEqual(['2', '4'], [m.envelop.id for m in result.messages])

    def test_tail_allowed_types_no_match_returns_empty(self):
        self._put('0', content_type='type_a')
        result = self.svc.tail('sess', 5, allowed_types=['type_b'])
        self.assertEqual([], result.messages)

    def test_get_allowed_types_matches_by_suffix(self):
        self._put('0', content_type='some.module.TypeA')
        self._put('1', content_type='some.module.TypeB')
        result = self.svc.get('sess', allowed_types=['.TypeA'], timeout_in_seconds=0)
        self.assertEqual(1, len(result.messages))
        self.assertEqual('0', result.messages[0].envelop.id)

    def test_get_allowed_types_suffix_no_match_returns_empty(self):
        self._put('0', content_type='some.module.TypeA')
        result = self.svc.get('sess', allowed_types=['.TypeB'], timeout_in_seconds=0.05)
        self.assertEqual([], result.messages)

    def test_tail_allowed_types_matches_by_suffix(self):
        self._put('0', content_type='some.module.TypeA')
        self._put('1', content_type='some.module.TypeB')
        self._put('2', content_type='some.module.TypeA')
        result = self.svc.tail('sess', 5, allowed_types=['.TypeA'])
        self.assertEqual(['0', '2'], [m.envelop.id for m in result.messages])

    def test_tail_allowed_types_suffix_no_match_returns_empty(self):
        self._put('0', content_type='some.module.TypeA')
        result = self.svc.tail('sess', 5, allowed_types=['.TypeB'])
        self.assertEqual([], result.messages)

    # --- multiple sessions ---

    def test_sessions_are_isolated(self):
        self._put('a1', session='a')
        self._put('b1', session='b')
        result_a = self.svc.get('a', timeout_in_seconds=0)
        result_b = self.svc.get('b', timeout_in_seconds=0)
        self.assertEqual(['a1'], [m.envelop.id for m in result_a.messages])
        self.assertEqual(['b1'], [m.envelop.id for m in result_b.messages])

    # --- aliases ---

    def test_aliases_resolve_short_name_on_put(self):
        svc = AvatarMessagingService(aliases={'A': MsgA})
        full = TypeTools.type_to_full_name(MsgA)
        svc.put(make_msg('1', content_type='A'))
        result = svc.get('sess', timeout_in_seconds=0)
        self.assertEqual(full, result.messages[0].content_type)

    def test_aliases_resolve_in_allowed_types(self):
        svc = AvatarMessagingService(aliases={'A': MsgA, 'B': MsgB})
        svc.put(make_msg('1', content_type='A'))
        svc.put(make_msg('2', content_type='B'))
        result = svc.get('sess', allowed_types=['A'], timeout_in_seconds=0)
        self.assertEqual(1, len(result.messages))
        self.assertEqual('1', result.messages[0].envelop.id)

    # --- tail with from_timestamp ---

    def test_tail_from_timestamp_returns_messages_at_or_after(self):
        self._put('0')
        self._put('1')
        sleep(0.02)
        ts = datetime.now()
        sleep(0.02)
        self._put('2')
        self._put('3')
        result = self.svc.tail('sess', from_timestamp=ts)
        self.assertEqual(['2', '3'], [m.envelop.id for m in result.messages])

    def test_tail_from_timestamp_before_all_returns_everything(self):
        self._put('0')
        self._put('1')
        self._put('2')
        ts = datetime(2000, 1, 1)
        result = self.svc.tail('sess', from_timestamp=ts)
        self.assertEqual(3, len(result.messages))

    def test_tail_from_timestamp_after_all_returns_empty(self):
        self._put('0')
        self._put('1')
        ts = datetime(2999, 1, 1)
        result = self.svc.tail('sess', from_timestamp=ts)
        self.assertEqual([], result.messages)

    def test_tail_from_timestamp_unknown_session_returns_missing_session(self):
        result = self.svc.tail('ghost', from_timestamp=datetime.now())
        self.assertTrue(result.missing_session)

    def test_no_aliases_does_not_crash(self):
        svc = AvatarMessagingService(aliases=None)
        svc.put(make_msg('1', content_type='whatever'))
        result = svc.get('sess', timeout_in_seconds=0)
        self.assertEqual(1, len(result.messages))
