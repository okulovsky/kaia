import unittest
from dataclasses import dataclass
from avatar.messaging import *

@dataclass
class In(IMessage):
    pass

@dataclass
class Out(IMessage):
    content: int


class TestWrongOutputType(unittest.TestCase):
    def check(self, function):
        client = TestStream().create_client()
        client.put(In())

        processor = AvatarProcessor(client)
        processor.rules.add(function, input=In)

        result = processor.debug_and_stop_by_count(1)
        return result.messages

    def test_one_message(self):
        def one_message(_):
            return Out(1)
        result = self.check(one_message)
        self.assertEqual(2, len(result))
        self.assertIsInstance(result[0], In)
        self.assertIsInstance(result[1], Out)

    def test_two_messages(self):
        def one_message(_):
            return Out(1), Out(2)
        result = self.check(one_message)
        self.assertEqual(3, len(result))
        self.assertIsInstance(result[0], In)
        self.assertIsInstance(result[1], Out)
        self.assertIsInstance(result[2], Out)
        self.assertEqual(1, result[1].content)
        self.assertEqual(2, result[2].content)

    def test_no_messages(self):
        def no_messages(_):
            return ()
        result = self.check(no_messages)
        self.assertEqual(1, len(result))
        self.assertIsInstance(result[0], In)

    def test_callable(self):
        class Test:
            def __call__(self, input: In):
                return Out(0)
        result = self.check(Test())
        self.assertEqual(2, len(result))
        self.assertIsInstance(result[0], In)
        self.assertIsInstance(result[1], Out)




