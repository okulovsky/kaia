import unittest

from creative_articulator.drama.data import Message
from creative_articulator.drama.driver import AddMessageDiff, PopDiff, SceneState, StoryState
from creative_articulator.drama.scene.implementations import Summarizer
from .support import build_driver, completed_question_answer, mock_setup, NPC_NAME


class TestMessageAddedSceneCompleted(unittest.TestCase):
    """
    A user message is added, the NPC's reply satisfies the Persuasion goal,
    so the scene is completed: the final postprocessor summarizes it and the
    scene is popped off the story.
    """

    def test_reply_is_generated_and_scene_is_completed_and_summarized(self):
        mock_llm = mock_setup(
            'Alright, I will leave the house now.',
            completed_question_answer(True),
            'Alex convinced Bob to leave the house.',
        )
        driver = build_driver(
            mock_llm,
            messages=[
                Message.from_text('Bob enters the room.', None, False),
                Message.from_text('Hi Alex.', NPC_NAME, False),
            ],
            final_postprocessor=Summarizer(mock_llm),
        )
        driver.reset()
        AddMessageDiff(Message.from_text('Bob, please leave the house.', 'Alex', True)).apply(driver.story)

        diffs = driver.generate_and_apply()

        diff_types = [type(d) for d in diffs]
        self.assertEqual(3, len(diffs))
        self.assertEqual(AddMessageDiff, diff_types[0])
        reply = diffs[0].message
        self.assertEqual(NPC_NAME, reply.speaker)
        self.assertEqual(
            Message.from_text('Alright, I will leave the house now.').content,
            reply.content,
        )

        summary_diff = diffs[1]
        self.assertEqual('SceneSummaryDiff', type(summary_diff).__name__)
        self.assertEqual('Alex convinced Bob to leave the house.', summary_diff.summary)

        self.assertEqual(PopDiff, diff_types[2])

        state = driver.story[SceneState]
        self.assertEqual(4, len(state.messages))
        self.assertEqual('Alex convinced Bob to leave the house.', state.summary)
        self.assertTrue(state.finalized)

        self.assertIsNone(driver.story[StoryState].current_node)
        self.assertTrue(driver.story[StoryState].finalized)


if __name__ == '__main__':
    unittest.main()
