import traceback
import unittest
from dataclasses import dataclass
from avatar.messaging import *

@dataclass
class InMessage(IMessage):
    content: str

@dataclass
class WrongOutput(IMessage):
    error: str


class TestWrongOutputType(unittest.TestCase):
    def check(self, function, expected_exception = None):
        stream = TestStream()
        client = stream.create_client()
        client.put(InMessage(content="bad"))

        processor = AvatarDaemon(client)


        with self.assertRaises(Exception) as cm:
            processor.rules.bind(function)
            processor.debug_and_stop_by_count(1)

        if expected_exception is not None:
            self.assertIn(expected_exception, str(cm.exception))



    def test_handler_returns_unexpected_type(self):
        def handler_returns_wrong_type(msg: InMessage) -> InMessage:
            return WrongOutput(error="not allowed")
        self.check(handler_returns_wrong_type, 'returned unexpected type')

    def test_handler_returns_non_message(self):
        def handler_returns_non_message(msg: InMessage) -> InMessage:
            return 12
        self.check(handler_returns_non_message, 'returned invalid type')

    def test_handler_raises(self):
        def handler_raises(msg: InMessage) -> InMessage:
            raise ValueError("TEST TEST")
        self.check(handler_raises, 'TEST TEST')

    def test_handler_wrong_signature(self):
        def handler_wrong_signature() -> InMessage:
            return InMessage("test")
        self.check(handler_wrong_signature, 'Callable must have exactly one argument (excluding self/cls)')








