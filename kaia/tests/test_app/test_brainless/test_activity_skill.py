from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.daemon import UtteranceEvent, ChatCommand, InitializationEvent, ImageService, UtteranceSequenceCommand
from kaia.skills.activity_skill import ActivityIntents, ActivityReplies
from kaia.tests.helper import Helper
from avatar.utils import slice
from yo_fluq import Query


class ActivitySkillTestCase(TestCase):
    def test_activity_skill(self):
        with Loc.create_test_folder() as folder:
            helper = Helper(folder, self, brainless=True)
            with helper.app.get_fork_app(None):
                client = helper.app.create_avatar_client()
                client.initialize()
                client.put(InitializationEvent())
                intro = client.query(5).feed(slice(lambda z: isinstance(z, ChatCommand)))
                #self.assertEqual(9, len(intro))

                client.put(UtteranceEvent(ActivityIntents.change_activity()))
                client.query(5).feed(slice(lambda z: isinstance(z, ImageService.NewImageCommand)))
                after = client.query(5).feed(slice(lambda z: isinstance(z, UtteranceSequenceCommand)))
                self.assertEqual(
                    after[-1].utterances_sequence.utterances[0].template,
                    ActivityReplies.activity_changed
                )

                client.put(UtteranceEvent(ActivityIntents.activity_request()))
                after = client.query(5).feed(slice(lambda z: isinstance(z, UtteranceSequenceCommand)))
                self.assertEqual(
                    after[-1].utterances_sequence.utterances[0].template,
                    ActivityReplies.current_activity
                )




