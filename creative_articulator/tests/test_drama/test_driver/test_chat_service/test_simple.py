import unittest

from avatar.daemon import ChatCommand, TextEvent, InitializationEvent
from .support import running_chat_service, push_and_collect_replies


class TestSimple(unittest.TestCase):
    def test_simple(self):
        with running_chat_service(self) as client:
            reply = push_and_collect_replies(client, TextEvent("Hello"))
            print(reply)
            self.assertEqual(2, len(reply))
            self.assertEqual("Character: Reply to: User: Hello", reply[1].text)

            reply = push_and_collect_replies(client, TextEvent("MANY(3)"))
            self.assertEqual(4, len(reply))
            self.assertEqual("Character: Reply to: User: MANY(3)", reply[1].text)
            self.assertEqual("Character: Reply #2 to: User: MANY(3)", reply[2].text)
            self.assertEqual("Character: Reply #3 to: User: MANY(3)", reply[3].text)


