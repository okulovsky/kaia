import threading
from dataclasses import dataclass
from time import sleep
from unittest import TestCase

from avatar.messaging.core import AvatarClient, IMessage, Confirmation
from avatar.app.messages import AvatarMessagingService, AvatarMessageRepository
from foundation_kaia.marshalling_2 import TypeTools


@dataclass
class MsgA(IMessage):
    value: str = ''


@dataclass
class MsgB(IMessage):
    value: str = ''


def make_client(svc=None):
    if svc is None:
        svc = AvatarMessagingService()
    return AvatarClient(AvatarMessageRepository(svc), 'sess')


class TestPullTailWrappers(TestCase):
    """pull() and tail() return plain lists, unlike base_pull/base_tail."""

    def test_pull_returns_list(self):
        client = make_client()
        client.push(MsgA('x'))
        result = client.pull(timeout_in_seconds=0)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], MsgA)

    def test_pull_returns_empty_list_on_timeout(self):
        client = make_client()
        client.push(MsgA('x'))
        client.pull(timeout_in_seconds=0)          # consume
        result = client.pull(timeout_in_seconds=0)
        self.assertEqual([], result)

    def test_tail_returns_list(self):
        client = make_client()
        for i in range(3):
            client.push(MsgA(str(i)))
        result = client.tail(2)
        self.assertIsInstance(result, list)
        self.assertEqual(2, len(result))
        self.assertIsInstance(result[0], MsgA)


class TestSetLastId(TestCase):

    def test_set_last_id_skips_earlier_messages(self):
        svc = AvatarMessagingService()
        writer = make_client(svc)
        for i in range(3):
            writer.push(MsgA(str(i)))

        # grab id of second message via a fresh reader
        reader = make_client(svc)
        msgs = reader.pull(timeout_in_seconds=0)
        second_id = msgs[1].envelop.id

        positioned = make_client(svc)
        positioned.set_last_id(second_id)
        result = positioned.pull(timeout_in_seconds=0)
        self.assertEqual(1, len(result))
        self.assertEqual('2', result[0].value)

    def test_set_last_id_to_none_resets_to_beginning(self):
        svc = AvatarMessagingService()
        client = make_client(svc)
        for i in range(3):
            client.push(MsgA(str(i)))
        client.pull(timeout_in_seconds=0)           # advance to end
        client.set_last_id(None)
        result = client.pull(timeout_in_seconds=0)
        self.assertEqual(3, len(result))


class TestClone(TestCase):

    def test_clone_starts_with_fresh_last_id(self):
        svc = AvatarMessagingService()
        client = make_client(svc)
        for i in range(3):
            client.push(MsgA(str(i)))
        client.pull(timeout_in_seconds=0)           # advance to end

        clone = client.clone_client()
        clone.set_last_id()
        result = clone.pull(timeout_in_seconds=0)
        self.assertEqual(3, len(result))            # clone sees all messages

    def test_clone_original_last_id_unaffected(self):
        svc = AvatarMessagingService()
        client = make_client(svc)
        for i in range(3):
            client.push(MsgA(str(i)))
        client.pull(timeout_in_seconds=0)
        original_last_id = client.last_id

        clone = client.clone_client()
        clone.set_last_id()
        clone.pull(timeout_in_seconds=0)            # clone advances its own last_id

        self.assertEqual(original_last_id, client.last_id)

    def test_clone_shares_service_and_session(self):
        svc = AvatarMessagingService()
        client = make_client(svc)
        clone = client.clone_client()
        clone.push(MsgA('from_clone'))
        result = client.pull(timeout_in_seconds=0)
        self.assertEqual(1, len(result))
        self.assertEqual('from_clone', result[0].value)

    def test_clone_inherits_allowed_types(self):
        full_a = TypeTools.type_to_full_name(MsgA)
        svc = AvatarMessagingService()
        client = AvatarClient(AvatarMessageRepository(svc), 'sess', allowed_types=[full_a])
        clone = client.clone_client()
        self.assertEqual(client.allowed_types, clone.allowed_types)


class TestScrollToEnd(TestCase):

    def test_scroll_to_end_on_empty_queue(self):
        client = make_client()
        client.scroll_to_end()
        # last_id is None — subsequent pull gets everything from start
        client.push(MsgA('after'))
        result = client.pull(timeout_in_seconds=0)
        self.assertEqual(1, len(result))
        self.assertEqual('after', result[0].value)

    def test_scroll_to_end_skips_existing_messages(self):
        client = make_client()
        for i in range(3):
            client.push(MsgA(str(i)))
        client.scroll_to_end()
        result = client.pull(timeout_in_seconds=0)
        self.assertEqual(0, len(result))

    def test_scroll_to_end_then_new_message_is_visible(self):
        client = make_client()
        for i in range(3):
            client.push(MsgA(str(i)))
        client.scroll_to_end()
        client.push(MsgA('new'))
        result = client.pull(timeout_in_seconds=0)
        self.assertEqual(1, len(result))
        self.assertEqual('new', result[0].value)


class TestQuery(TestCase):

    def test_query_collects_all_pre_existing_messages(self):
        client = make_client()
        for i in range(3):
            client.push(MsgA(str(i)))
        result = client.query(time_limit_in_seconds=0.5, no_exception=True).to_list()
        self.assertEqual(3, len(result))
        self.assertIsInstance(result[0], MsgA)

    def test_query_no_exception_returns_empty_when_nothing_arrives(self):
        client = make_client()
        result = client.query(time_limit_in_seconds=0.25, no_exception=True).to_list()
        self.assertEqual([], result)

    def test_query_raises_value_error_on_timeout_with_no_messages(self):
        client = make_client()
        with self.assertRaises(ValueError) as ctx:
            client.query(time_limit_in_seconds=0.25).to_list()
        self.assertIn('NO MESSAGES RECEIVED', str(ctx.exception))

    def test_query_raises_value_error_contains_time_limit_text(self):
        client = make_client()
        with self.assertRaises(ValueError) as ctx:
            client.query(time_limit_in_seconds=0.25).to_list()
        self.assertIn('Time limit exceed', str(ctx.exception))

    def test_query_collects_messages_arriving_from_background_thread(self):
        client = make_client()
        collected = []

        def push_later():
            sleep(0.05)
            for i in range(3):
                client.push(MsgA(str(i)))

        t = threading.Thread(target=push_later, daemon=True)
        t.start()

        for msg in client.query(time_limit_in_seconds=0.6, no_exception=True):
            collected.append(msg)

        t.join(timeout=2)
        self.assertEqual(3, len(collected))


class TestWaitForConfirmation(TestCase):

    def _setup(self):
        svc = AvatarMessagingService()
        return AvatarClient(AvatarMessageRepository(svc), 'sess'), svc

    def test_wait_for_confirmation_returns_confirmation(self):
        client, svc = self._setup()
        request = MsgA('req')
        client.push(request)

        def respond():
            sleep(0.05)
            AvatarClient(AvatarMessageRepository(svc), 'sess').push(Confirmation().as_confirmation_for(request))

        t = threading.Thread(target=respond, daemon=True)
        t.start()
        result = client.wait_for_confirmation(request, time_limit_in_seconds=1)
        t.join(timeout=2)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, Confirmation)

    def test_wait_for_confirmation_typed_result(self):
        client, svc = self._setup()
        request = MsgA('req')
        client.push(request)

        def respond():
            sleep(0.05)
            AvatarClient(AvatarMessageRepository(svc), 'sess').push(Confirmation(result=42).as_confirmation_for(request))

        t = threading.Thread(target=respond, daemon=True)
        t.start()
        result = client.wait_for_confirmation(request, _type=Confirmation, time_limit_in_seconds=1)
        t.join(timeout=2)

        self.assertIsInstance(result, Confirmation)
        self.assertEqual(42, result.result)

    def test_wait_for_confirmation_no_exceptions_returns_none_on_timeout(self):
        client, _ = self._setup()
        request = MsgA('req')
        client.push(request)
        # nobody sends a confirmation
        result = client.wait_for_confirmation(request, time_limit_in_seconds=0.3, no_exceptions=True)
        self.assertIsNone(result)

    def test_wait_for_confirmation_ignores_unrelated_messages(self):
        client, svc = self._setup()
        request = MsgA('req')
        client.push(request)

        def respond():
            sleep(0.05)
            responder = AvatarClient(AvatarMessageRepository(svc), 'sess')
            responder.push(MsgA('noise'))       # unrelated
            sleep(0.05)
            responder.push(Confirmation().as_confirmation_for(request))

        t = threading.Thread(target=respond, daemon=True)
        t.start()
        result = client.wait_for_confirmation(request, time_limit_in_seconds=1)
        t.join(timeout=2)

        self.assertIsInstance(result, Confirmation)


class TestRunSynchronously(TestCase):

    def _autoconfirm(self, svc):
        """Daemon thread that auto-confirms every non-confirmation message."""
        responder = AvatarClient(AvatarMessageRepository(svc), 'sess')

        def loop():
            while True:
                msgs = responder.pull(timeout_in_seconds=0.1)
                for msg in msgs:
                    if msg.envelop.confirmation_for is None:
                        responder.push(Confirmation(result='ok').as_confirmation_for(msg))

        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def test_run_synchronously_returns_confirmation(self):
        svc = AvatarMessagingService()
        client = AvatarClient(AvatarMessageRepository(svc), 'sess')
        self._autoconfirm(svc)

        result = client.run_synchronously(MsgA('hello'), _type=Confirmation, time_limit_in_seconds=2)
        self.assertIsInstance(result, Confirmation)
        self.assertEqual('ok', result.result)

    def test_run_synchronously_pushes_message_before_waiting(self):
        svc = AvatarMessagingService()
        client = AvatarClient(AvatarMessageRepository(svc), 'sess')
        observer = AvatarClient(AvatarMessageRepository(svc), 'sess')
        self._autoconfirm(svc)

        client.run_synchronously(MsgA('ping'), time_limit_in_seconds=2)

        # The original request must be visible in the session
        all_msgs = observer.pull(timeout_in_seconds=0)
        types = [type(m) for m in all_msgs]
        self.assertIn(MsgA, types)


class TestDefault(TestCase):

    def test_default_session_is_default(self):
        client = AvatarClient.default()
        self.assertEqual('default', client.session)

    def test_default_ttl_is_none(self):
        client = AvatarClient.default()
        self.assertIsNone(client.repo.service.ttl_in_seconds)

    def test_default_client_can_push_and_pull(self):
        client = AvatarClient.default()
        client.push(MsgA('hi'))
        result = client.pull(timeout_in_seconds=0)
        self.assertEqual(1, len(result))
