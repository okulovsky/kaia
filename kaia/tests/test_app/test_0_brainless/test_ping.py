from kaia.app import KaiaAppSettings
from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.services import UtteranceEvent, ChatCommand
from kaia.skills.ping import PingIntents

def slice(condition, hit_count: int = 1):
    def _(q):
        hits = 0
        result = []
        for e in q:
            result.append(e)
            if condition(e):
                hits+=1
                if hits>=hit_count:
                    return result
    return _

class PingBrainlessTestCase(TestCase):
    def test_ping(self):
        settings = KaiaAppSettings()
        settings.brainbox = None
        settings.phonix = None
        settings.avatar_processor.initialization_event_at_startup = False
        settings.avatar_processor.timer_event_span_in_seconds = None
        with Loc.create_test_folder() as folder:
            app = settings.create_app(folder)
            with app.get_fork_app(None):
                app.avatar_api.wait()

                app.avatar_stream.put(UtteranceEvent(PingIntents.question()))
                client = app.avatar_stream.create_client()
                result = client.query(5).where(lambda z: isinstance(z, ChatCommand)).take(2).to_list()
                self.assertEqual("Are you here?", result[0].text)
                self.assertEqual(ChatCommand.MessageType.from_user, result[0].type)

                self.assertEqual("Sure, I'm listening.", result[1].text)
                self.assertEqual(ChatCommand.MessageType.to_user, result[1].type)

    def test_ping_with_initialization(self):
        settings = KaiaAppSettings()
        settings.brainbox = None
        settings.phonix = None
        settings.avatar_processor.timer_event_span_in_seconds = None

        with Loc.create_test_folder() as folder:
            app = settings.create_app(folder)
            with app.get_fork_app(None):
                app.avatar_api.wait()
                client = app.avatar_stream.create_client()
                client.query(5).take(8).to_list()

                client.put(UtteranceEvent(PingIntents.question()))
                self.assertIsInstance(client.pull()[0], UtteranceEvent)

                result = client.query(5).where(lambda z: isinstance(z, ChatCommand)).take(2).to_list()
                self.assertEqual('/static/unknown.png', result[0].sender_avatar_file_id)
                self.assertEqual('/static/unknown.png', result[1].sender_avatar_file_id)




