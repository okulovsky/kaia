import unittest

from creative_articulator.drama.data import Message
from creative_articulator.drama.driver import AddMessageDiff, SceneState, StoryState
from creative_articulator.drama.scene import SceneSettings
from creative_articulator.drama.scene.implementations import SceneShorteningPostprocessor
from .support import build_driver, completed_question_answer, mock_setup, NPC_NAME


class TestMessageAddedSceneShortened(unittest.TestCase):
    """
    A user message is added, the NPC replies, the scene is not completed, but
    with the message count now above the (deliberately low, for the test)
    shortening threshold, the regular postprocessor shortens the scene.
    """

    def test_reply_is_generated_and_scene_is_shortened(self):
        mock_llm = mock_setup(
            'Fine, let us talk about it a bit more.',
            completed_question_answer(False),
            'Alex asked Bob to leave, and Bob is hesitant.',
        )
        settings = SceneSettings(min_messages_for_shortening=3, min_messages_after_shortening=2)
        driver = build_driver(
            mock_llm,
            messages=[
                Message.from_text('Bob enters the room.', None, False),
                Message.from_text('Hi Alex.', NPC_NAME, False),
            ],
            settings=settings,
            regular_postprocessor=SceneShorteningPostprocessor(mock_llm),
        )
        driver.reset()
        AddMessageDiff(Message.from_text('Bob, please leave the house.', 'Alex', True)).apply(driver.story)

        diffs = driver.generate_and_apply()

        diff_types = [type(d) for d in diffs]
        self.assertEqual(2, len(diffs))
        self.assertEqual(AddMessageDiff, diff_types[0])
        reply = diffs[0].message
        self.assertEqual(NPC_NAME, reply.speaker)
        self.assertEqual(
            Message.from_text('Fine, let us talk about it a bit more.').content,
            reply.content,
        )

        shortening_diff = diffs[1]
        self.assertEqual('SceneShorteningDiff', type(shortening_diff).__name__)
        self.assertEqual(2, shortening_diff.shortening_index)
        self.assertEqual('Alex asked Bob to leave, and Bob is hesitant.', shortening_diff.shortening)

        state = driver.story[SceneState]
        self.assertEqual(4, len(state.messages))
        self.assertEqual(2, state.shortening_index)
        self.assertEqual('Alex asked Bob to leave, and Bob is hesitant.', state.shortening)
        self.assertFalse(state.finalized)
        self.assertIsNone(state.summary)

        self.assertIs(driver.story, driver.story[StoryState].current_node)
        self.assertFalse(driver.story[StoryState].finalized)


if __name__ == '__main__':
    unittest.main()
