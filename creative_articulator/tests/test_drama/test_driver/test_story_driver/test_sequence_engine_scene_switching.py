import unittest

from creative_articulator.drama.data import Node, Message
from creative_articulator.drama.driver import (
    StoryDriver, MockEngine, SequenceEngine, IEngine,
    StoryState, SceneState, AddMessageDiff, PushDiff, PopDiff,
)

from .support import run_generation


def _build_story() -> Node:
    """root (SequenceEngine) -> [child1 (MockEngine/Alice), child2 (MockEngine/Bob)]"""
    root = Node()
    root.attach(SequenceEngine(), custom_type=IEngine)

    child1 = Node()
    child1.attach(MockEngine(buffer_message=0, character_name="Alice"), custom_type=IEngine)
    root.append(child1)

    child2 = Node()
    child2.attach(MockEngine(buffer_message=0, character_name="Bob"), custom_type=IEngine)
    root.append(child2)

    return root


def _send_user_message(driver: StoryDriver, text: str):
    AddMessageDiff(Message.from_text(text, "User", True)).apply(driver.story)


class TestSequenceEngineSceneSwitching(unittest.TestCase):
    def test_switches_from_one_mock_scene_to_the_next(self):
        driver = StoryDriver(_build_story())
        driver.reset()

        first_turn = run_generation(driver)
        self.assertEqual(
            [PushDiff, AddMessageDiff, AddMessageDiff],
            [type(d) for d in first_turn],
        )
        first_child, second_child = driver.story.children
        self.assertIs(first_child, driver.story[StoryState].current_node)
        self.assertEqual(2, len(first_child[SceneState].messages))

        _send_user_message(driver, "POP")
        second_turn = run_generation(driver)

        self.assertEqual(
            [AddMessageDiff, PopDiff, PushDiff, AddMessageDiff, AddMessageDiff],
            [type(d) for d in second_turn],
        )

        self.assertTrue(first_child[SceneState].finalized)
        self.assertFalse(second_child[SceneState].finalized)
        self.assertIs(second_child, driver.story[StoryState].current_node)
        self.assertEqual(2, len(second_child[SceneState].messages))
        self.assertFalse(driver.story[StoryState].finalized)

        opening = second_turn[3].message
        self.assertIsNone(opening.speaker)
        self.assertEqual(Message.from_text("* Opening *").content, opening.content)

        reply = second_turn[4].message
        self.assertEqual("Bob", reply.speaker)
        self.assertEqual(
            Message.from_text("Reply to: " + str(opening)).content,
            reply.content,
        )

    def test_story_finalizes_once_last_scene_is_popped(self):
        driver = StoryDriver(_build_story())
        driver.reset()

        run_generation(driver)
        _send_user_message(driver, "POP")
        run_generation(driver)
        _send_user_message(driver, "POP")
        third_turn = run_generation(driver)

        self.assertEqual(
            [AddMessageDiff, PopDiff, PopDiff],
            [type(d) for d in third_turn],
        )

        self.assertIsNone(driver.story[StoryState].current_node)
        self.assertTrue(driver.story[StoryState].finalized)
        for child in driver.story.children:
            self.assertTrue(child[SceneState].finalized)

        # A finalized story yields nothing more and must not raise.
        self.assertEqual([], run_generation(driver))


if __name__ == '__main__':
    unittest.main()
