import unittest

from creative_articulator.drama.data import Message
from creative_articulator.drama.driver import AddMessageDiff, SceneState, StoryState
from .support import build_driver, completed_question_answer, mock_setup, NPC_NAME


class TestMessageAddedSceneContinues(unittest.TestCase):
    """
    A user message is added after the scene's opening exchange. The NPC
    replies, but the scene is neither completed nor shortened: no
    postprocessor is configured, since none is exercised here.
    """

    def test_reply_is_generated_and_scene_stays_open(self):
        mock_llm = mock_setup(
            'Fine, give me a moment to think about it.',
            completed_question_answer(False),
        )
        driver = build_driver(
            mock_llm,
            messages=[
                Message.from_text('Bob enters the room.', None, False),
                Message.from_text('Hi Alex.', NPC_NAME, False),
            ],
        )
        driver.reset()
        AddMessageDiff(Message.from_text('Bob, please leave the house.', 'Alex', True)).apply(driver.story)

        diffs = driver.generate_and_apply()

        self.assertEqual([AddMessageDiff], [type(d) for d in diffs])
        reply = diffs[0].message
        self.assertEqual(NPC_NAME, reply.speaker)
        self.assertFalse(reply.from_user)
        self.assertEqual(
            Message.from_text('Fine, give me a moment to think about it.').content,
            reply.content,
        )

        state = driver.story[SceneState]
        self.assertEqual(4, len(state.messages))
        self.assertEqual(
            Message.from_text('Bob, please leave the house.').content,
            state.messages[-2].content,
        )
        self.assertIs(reply, state.messages[-1])
        self.assertFalse(state.finalized)
        self.assertIsNone(state.shortening)
        self.assertIsNone(state.summary)

        self.assertIs(driver.story, driver.story[StoryState].current_node)
        self.assertFalse(driver.story[StoryState].finalized)


if __name__ == '__main__':
    unittest.main()
