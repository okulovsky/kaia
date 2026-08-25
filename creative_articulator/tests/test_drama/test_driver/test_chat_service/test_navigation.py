import unittest

from avatar.daemon import ChatCommand, TextEvent
from creative_articulator.drama.driver import (
    SwipeChatMessageEvent, DeleteChatMessageEvent, DeleteChatMessagesCommand,
)
from .support import running_chat_service, push_and_collect_replies


def _build_branch(client):
    """
    Builds root -> A -> [echo -> reply, alt], with alt (a fresh leaf) currently selected.
    Returns (echo_id, reply_id, alt_id).
    """
    echo, reply = push_and_collect_replies(client, TextEvent("Hello"))
    hide, alt = push_and_collect_replies(client, SwipeChatMessageEvent(echo.message_id, swipe_to_left=False))
    return echo.message_id, reply.message_id, alt.message_id


class TestNavigation(unittest.TestCase):
    def test_switch_back_to_original_branch(self):
        with running_chat_service(self) as client:
            echo_id, reply_id, alt_id = _build_branch(client)

            events = push_and_collect_replies(client, SwipeChatMessageEvent(alt_id, swipe_to_left=True))
            self.assertEqual(3, len(events))
            hide, show1, show2 = events

            self.assertIsInstance(hide, DeleteChatMessagesCommand)
            self.assertEqual(hide.ids, [alt_id])

            self.assertIsInstance(show1, ChatCommand)
            self.assertEqual(show1.message_id, echo_id)
            self.assertIsInstance(show2, ChatCommand)
            self.assertEqual(show2.message_id, reply_id)

    def test_switch_forward_to_alternative_branch(self):
        with running_chat_service(self) as client:
            echo_id, reply_id, alt_id = _build_branch(client)

            # First go back to the original branch, then forward again
            push_and_collect_replies(client, SwipeChatMessageEvent(alt_id, swipe_to_left=True))

            events = push_and_collect_replies(client, SwipeChatMessageEvent(echo_id, swipe_to_left=False))
            self.assertEqual(2, len(events))
            hide, show = events

            self.assertIsInstance(hide, DeleteChatMessagesCommand)
            self.assertCountEqual(hide.ids, [echo_id, reply_id])

            self.assertIsInstance(show, ChatCommand)
            self.assertEqual(show.message_id, alt_id)

    def test_delete_leaf(self):
        with running_chat_service(self) as client:
            echo_id, reply_id, alt_id = _build_branch(client)

            # alt is one of two floor members under root (the other being echo,
            # already hidden from the earlier swipe); deleting it wipes the
            # whole floor, so a fresh replacement is generated from root.
            events = push_and_collect_replies(client, DeleteChatMessageEvent(alt_id))
            self.assertEqual(2, len(events))
            hide, show = events

            self.assertIsInstance(hide, DeleteChatMessagesCommand)
            self.assertEqual(hide.ids, [alt_id])

            # Deleting the leaf immediately triggers generation of its replacement
            self.assertIsInstance(show, ChatCommand)
            self.assertNotEqual(show.message_id, alt_id)

            # echo's branch was wiped out along with alt, so it's gone for good
            events = push_and_collect_replies(client, SwipeChatMessageEvent(show.message_id, swipe_to_left=True))
            self.assertEqual(0, len(events))

    def test_delete_branch_node(self):
        with running_chat_service(self) as client:
            echo_id, reply_id, alt_id = _build_branch(client)

            # Switch to the original branch so we can delete the echo from there
            push_and_collect_replies(client, SwipeChatMessageEvent(alt_id, swipe_to_left=True))

            # echo and alt are both children of root (one floor); deleting echo
            # wipes the whole floor -- including alt -- so root regenerates fresh
            # rather than falling back to alt.
            events = push_and_collect_replies(client, DeleteChatMessageEvent(echo_id))
            self.assertEqual(2, len(events))
            hide, show = events

            self.assertIsInstance(hide, DeleteChatMessagesCommand)
            self.assertCountEqual(hide.ids, [echo_id, reply_id])

            self.assertIsInstance(show, ChatCommand)
            self.assertNotIn(show.message_id, (echo_id, alt_id))

            # alt was wiped out along with echo, so it's gone for good
            events = push_and_collect_replies(client, SwipeChatMessageEvent(show.message_id, swipe_to_left=True))
            self.assertEqual(0, len(events))


if __name__ == '__main__':
    unittest.main()
