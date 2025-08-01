import unittest
import time
import threading
from avatar.messaging.stream import TestStream, IMessage

class TestMessage(IMessage):
    pass

class TestStreamTestCase(unittest.TestCase):

    def setUp(self):
        self.stream = TestStream()

    def test_put_and_get(self):
        e1 = TestMessage()
        e2 = TestMessage()

        self.stream.put(e1)
        self.stream.put(e2)

        result = self.stream.get()
        self.assertEqual(result, [e1, e2])

    def test_get_from_last_id(self):
        e1 = TestMessage()
        e2 = TestMessage()
        e3 = TestMessage()

        self.stream.put(e1)
        self.stream.put(e2)
        self.stream.put(e3)

        partial = self.stream.get(last_id=e1.envelop.id)
        self.assertEqual(partial, [e2, e3])

    def test_stream_client_pull(self):
        e1 = TestMessage()
        e2 = TestMessage()
        self.stream.put(e1)
        self.stream.put(e2)

        client = self.stream.create_client()
        pulled = client.pull()
        self.assertEqual([e1, e2], pulled)

        # Pull again, should return nothing new
        client.last_id = e2.envelop.id
        self.assertEqual([], client.pull())

    def test_put_sync_confirms(self):
        """
        Simulate a confirmation being added asynchronously.
        """
        source = TestMessage()

        def add_confirmation():
            time.sleep(0.05)
            confirm_envelop = TestMessage().as_confirmation_for(source)
            self.stream.put(confirm_envelop)

        threading.Thread(target=add_confirmation).start()

        confirmation = self.stream.create_client().run_synchronously(source)

        self.assertEqual(confirmation.envelop.confirmation_for, (source.envelop.id,))

    def test_put_sync_confirms_chain(self):
        """
        Simulate a confirmation being added asynchronously.
        """
        source = TestMessage()

        def add_confirmation():
            time.sleep(0.05)
            intermediate = TestMessage().as_propagation_confirmation_to(source)
            self.stream.put(intermediate)
            time.sleep(0.05)
            self.stream.put(TestMessage().as_confirmation_for(intermediate))

        threading.Thread(target=add_confirmation).start()

        confirmation = self.stream.create_client().run_synchronously(source)

        self.assertIn(source.envelop.id, confirmation.envelop.confirmation_for)

