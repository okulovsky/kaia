from kaia.app import KaiaAppSettings
from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.daemon import UtteranceEvent, ChatCommand
from kaia.skills.ping import PingIntents
from kaia.tests.helper import Helper


class PingBrainlessTestCase(TestCase):
    def test_ping(self):
        with Loc.create_test_folder() as folder:
            helper = Helper(folder, self, brainless=True)
            with helper.app.get_fork_app(None):
                client = helper.app.create_avatar_client()
                client.initialize()
                client.put(UtteranceEvent(PingIntents.question()))

                result = client.query(5).where(lambda z: isinstance(z, ChatCommand)).take(2).to_list()
                self.assertEqual("Are you here?", result[0].text)
                self.assertEqual(ChatCommand.MessageType.from_user, result[0].type)

                self.assertEqual("Sure, I'm listening.", result[1].text)
                self.assertEqual(ChatCommand.MessageType.to_user, result[1].type)


    def test_ping_with_initialization(self):
        with Loc.create_test_folder() as folder:
            helper = Helper(folder, self, brainless=True)
            with helper.app.get_fork_app(None):
                client = helper.app.create_avatar_client()
                client.initialize()

                utterance = client.put(UtteranceEvent(PingIntents.question()))
                self.assertIsInstance(client.pull()[0], UtteranceEvent)

                result = client.query(5).where(lambda z: isinstance(z, ChatCommand)).take(2).to_list()
                self.assertEqual('/static/unknown.png', result[0].sender_avatar_file_id)
                self.assertEqual('/static/unknown.png', result[1].sender_avatar_file_id)




