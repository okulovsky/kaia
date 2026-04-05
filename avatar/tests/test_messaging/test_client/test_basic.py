from dataclasses import dataclass
from datetime import datetime
from time import sleep
from unittest import TestCase

from avatar.app.messages import *
from avatar.messaging.core import AvatarClient, IMessage, Envelop
from foundation_kaia.marshalling_2 import TypeTools


@dataclass
class MsgA(IMessage):
    value: str = ''


@dataclass
class MsgB(IMessage):
    value: str = ''


class TestClient(TestCase):

    def _client(self, allowed_types=None):
        client = AvatarClient.default()
        client.allowed_types = allowed_types
        return client

    def test_push_and_pull_round_trip(self):
        client = self._client()
        client.push(MsgA('hello'))
        result = client.base_pull(timeout_in_seconds=0)
        self.assertEqual(1, len(result.messages))
        self.assertIsInstance(result.messages[0], MsgA)
        self.assertEqual('hello', result.messages[0].value)

    def test_pull_advances_last_id(self):
        client = self._client()
        client.push(MsgA('first'))
        client.push(MsgA('second'))
        r1 = client.base_pull(timeout_in_seconds=0)
        self.assertEqual(2, len(r1.messages))
        r2 = client.base_pull(timeout_in_seconds=0)
        self.assertEqual(0, len(r2.messages))

    def test_pull_max_messages(self):
        client = self._client()
        for i in range(5):
            client.push(MsgA(str(i)))
        result = client.base_pull(max_messages=2, timeout_in_seconds=0)
        self.assertEqual(2, len(result.messages))

    def test_pull_after_max_messages_continues_from_correct_position(self):
        client = self._client()
        for i in range(4):
            client.push(MsgA(str(i)))
        r1 = client.base_pull(max_messages=2, timeout_in_seconds=0)
        self.assertEqual(['0', '1'], [m.value for m in r1.messages])
        r2 = client.base_pull(timeout_in_seconds=0)
        self.assertEqual(['2', '3'], [m.value for m in r2.messages])

    def test_pull_allowed_types_filters_messages(self):
        full_a = TypeTools.type_to_full_name(MsgA)
        client = self._client([full_a])
        client.push(MsgA('a'))
        client.push(MsgB('b'))
        result = client.base_pull(timeout_in_seconds=0)
        self.assertEqual(1, len(result.messages))
        self.assertIsInstance(result.messages[0], MsgA)

    def test_pull_unknown_type_becomes_generic_message(self):
        client = self._client()
        client.repo.service.put(AvatarMessage(
            session='default', content_type='some.Unknown.Type',
            envelop=Envelop(id='x'), content={'k': 'v'}
        ))
        result = client.base_pull(timeout_in_seconds=0)
        self.assertEqual(1, len(result.messages))
        self.assertIsInstance(result.messages[0], GenericMessage)
        self.assertEqual('some.Unknown.Type', result.messages[0].content_type)

    def test_pull_preserves_envelop(self):
        msg = MsgA('test')
        client = self._client()
        client.push(msg)
        result = client.base_pull(timeout_in_seconds=0)
        self.assertEqual(msg.envelop.id, result.messages[0].envelop.id)

    def test_mixed_message_types_deserialized_correctly(self):
        client = self._client()
        client.push(MsgA('from_a'))
        client.push(MsgB('from_b'))
        result = client.base_pull(timeout_in_seconds=0)
        self.assertIsInstance(result.messages[0], MsgA)
        self.assertIsInstance(result.messages[1], MsgB)
        self.assertEqual('from_a', result.messages[0].value)
        self.assertEqual('from_b', result.messages[1].value)

    def test_tail_returns_last_n(self):
        client = self._client()
        for i in range(5):
            client.push(MsgA(str(i)))
        result = client.base_tail(3)
        self.assertEqual(3, len(result.messages))
        self.assertIsInstance(result.messages[0], MsgA)

    def test_tail_from_timestamp_returns_messages_after_cutoff(self):
        client = self._client()
        client.push(MsgA('early'))
        client.push(MsgA('also_early'))
        sleep(0.02)
        ts = datetime.now()
        sleep(0.02)
        client.push(MsgA('late'))
        result = client.tail(from_timestamp=ts)
        self.assertEqual(1, len(result))
        self.assertIsInstance(result[0], MsgA)
        self.assertEqual('late', result[0].value)

    def test_tail_from_timestamp_before_all_returns_all(self):
        client = self._client()
        client.push(MsgA('x'))
        client.push(MsgA('y'))
        result = client.tail(from_timestamp=datetime(2000, 1, 1))
        self.assertEqual(2, len(result))

    def test_with_types_stores_full_type_names(self):
        client = self._client()
        client.with_types(MsgA, MsgB)
        full_a = TypeTools.type_to_full_name(MsgA)
        full_b = TypeTools.type_to_full_name(MsgB)
        self.assertIn(full_a, client.allowed_types)
        self.assertIn(full_b, client.allowed_types)

    def test_with_types_filters_pull(self):
        client = self._client()
        client.with_types(MsgA)
        client.push(MsgA('keep'))
        client.push(MsgB('drop'))
        result = client.pull(timeout_in_seconds=0)
        self.assertEqual(1, len(result))
        self.assertIsInstance(result[0], MsgA)

    def test_missing_session_propagated_on_first_pull(self):
        client = self._client()
        result = client.base_pull(timeout_in_seconds=0)
        self.assertTrue(result.missing_session)
        self.assertFalse(result.missing_id)
