import unittest

from avatar.daemon import ChatCommand, TextEvent
from creative_articulator.drama.driver import SwipeChatMessageEvent, DeleteChatMessagesCommand
from .support import running_chat_service, push_and_collect_replies


class TestChatServiceBranchSwitch(unittest.TestCase):
    def test_chain_then_branch_at_second_message(self):
        with running_chat_service(self) as client:
            turn = push_and_collect_replies(client, TextEvent("Hello"))
            self.assertEqual(2, len(turn))
            echo, reply = turn
            self.assertEqual("User: Hello", echo.text)
            self.assertEqual("Character: Reply to: User: Hello", reply.text)

            # Swipe right at the echoed message: no existing alternative, so hide
            # [echo, reply] and let the engine generate a replacement.
            branch = push_and_collect_replies(client, SwipeChatMessageEvent(echo.message_id, swipe_to_left=False))
            self.assertEqual(2, len(branch))
            hide, new_reply = branch

            self.assertIsInstance(hide, DeleteChatMessagesCommand)
            self.assertCountEqual(hide.ids, [echo.message_id, reply.message_id])

            self.assertIsInstance(new_reply, ChatCommand)
            self.assertNotEqual(new_reply.message_id, echo.message_id)
            self.assertEqual("(1) 2/2", new_reply.details)


if __name__ == '__main__':
    unittest.main()
