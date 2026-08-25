import unittest

from avatar.daemon import TextEvent
from creative_articulator.drama.driver import ChatConfirmation, DeleteChatMessageEvent
from .support import running_chat_service, push_and_collect_replies, collect_results


class TestConcurrency(unittest.TestCase):
    def test_delete_message_while_reply_is_being_generated(self):
        with running_chat_service(self, time_to_message_in_seconds=1) as client:
            echo, reply = push_and_collect_replies(client, TextEvent("Hello"))

            # MANY(5) would normally produce 6 ChatCommands (the echo plus 5
            # replies) plus its own confirmation, 7 messages total. Deleting
            # `reply` -- the node the whole exchange hangs off of --
            # concurrently must cut that generation short.
            many_event = TextEvent("MANY(5)")
            delete_event = DeleteChatMessageEvent(reply.message_id)
            client.push(many_event)
            client.push(delete_event)

            many_results, delete_results = collect_results(client, many_event, delete_event, timeout=10)

            self.assertLess(len(many_results), 7, f"MANY(5) was not interrupted: {many_results}")
            self.assertIsInstance(many_results[-1], ChatConfirmation)
            self.assertTrue(many_results[-1].interrupted)

            self.assertIsInstance(delete_results[-1], ChatConfirmation)
            self.assertFalse(delete_results[-1].interrupted)


if __name__ == '__main__':
    unittest.main()
