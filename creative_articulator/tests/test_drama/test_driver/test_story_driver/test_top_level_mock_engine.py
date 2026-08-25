import unittest

from creative_articulator.drama.data import Node, Message
from creative_articulator.drama.driver import (
    StoryDriver, MockEngine, IEngine, StoryState, SceneState, AddMessageDiff,
)

from .support import run_generation


class TestTopLevelMockEngine(unittest.TestCase):
    """
    MockEngine is attached directly to the root node (no SequenceEngine in
    between), so StoryDriver.generate() drives it as the story's only scene.
    """

    def test_generates_opening_buffer_and_reply_then_waits(self):
        story = Node()
        story.attach(MockEngine(buffer_message=2, character_name="Alice"), custom_type=IEngine)

        driver = StoryDriver(story)
        driver.reset()

        results = run_generation(driver)

        self.assertEqual([AddMessageDiff] * 4, [type(d) for d in results])
        opening, buffer0, buffer1, reply = (d.message for d in results)

        self.assertIsNone(opening.speaker)
        self.assertEqual(Message.from_text("* Opening *").content, opening.content)

        self.assertEqual("Alice", buffer0.speaker)
        self.assertEqual(Message.from_text("Buffer message #0").content, buffer0.content)

        self.assertEqual("Alice", buffer1.speaker)
        self.assertEqual(Message.from_text("Buffer message #1").content, buffer1.content)

        self.assertEqual("Alice", reply.speaker)
        self.assertEqual(
            Message.from_text("Reply to: " + str(buffer1)).content,
            reply.content,
        )

        # No PushDiff/PopDiff was yielded, so the story stays at its root node.
        self.assertIs(driver.story, driver.story[StoryState].current_node)
        self.assertFalse(driver.story[StoryState].finalized)
        self.assertEqual(4, len(driver.story[SceneState].messages))

    def test_many_pattern_produces_extra_replies_before_waiting(self):
        story = Node()
        story.attach(MockEngine(buffer_message=0, character_name="Alice"), custom_type=IEngine)

        driver = StoryDriver(story)
        driver.reset()
        run_generation(driver)  # consumes the opening message and its automatic reply

        AddMessageDiff(Message.from_text("MANY(3)", "User", True)).apply(driver.story)
        results = run_generation(driver)

        self.assertEqual([AddMessageDiff] * 3, [type(d) for d in results])
        first, second, third = (d.message for d in results)
        self.assertIn("Reply to:", str(first))
        self.assertIn("Reply #2 to:", str(second))
        self.assertIn("Reply #3 to:", str(third))
        self.assertEqual(6, len(driver.story[SceneState].messages))


if __name__ == '__main__':
    unittest.main()
