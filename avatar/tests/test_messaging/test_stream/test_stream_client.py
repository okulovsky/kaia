import unittest
import time
import threading
from avatar.messaging.stream import TestStream, IMessage


class TestMessage(IMessage):
    pass



class TestStreamTestCase(unittest.TestCase):
    def autoconfirm(self: TestStream):
        client = self.stream.create_client()
        while True:
            msgs = client.pull()
            for msg in msgs:
                if msg.envelop.confirmation_for is None:
                    client.put(TestMessage().as_confirmation_for(msg))


    def setUp(self):
        self.stream = TestStream()
        thread = threading.Thread(target=self.autoconfirm, daemon=True)
        thread.start()

    def test_wait_for_confirmation(self):
        client = self.stream.create_client()
        msg = TestMessage()
        client.put(msg)
        client.wait_for_confirmation(msg, time_limit_in_seconds=0.5)


