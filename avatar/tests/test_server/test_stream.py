from avatar.daemon import SoundCommand, UtteranceEvent, PlayableTextMessage, TextInfo, TextEvent
from avatar.server import AvatarApi, AvatarServerSettings, AvatarStream, MessagingComponent
from unittest import TestCase
from foundation_kaia.misc import Loc

class AvatarStreamTestCase(TestCase):
    def test_stream(self):
        with Loc.create_test_file() as filename:
            settings = AvatarServerSettings((
                MessagingComponent(filename),
            ))
            with AvatarApi.Test(settings) as api:
                client = AvatarStream(api, 'test').create_client()
                client.put(SoundCommand('test'))
                messages = client.pull()
                self.assertIsInstance(messages[0], SoundCommand)

    def test_stream_scroll_down(self):
        with Loc.create_test_file() as filename:
            with AvatarApi.Test() as api:
                client = AvatarStream(api, 'test').create_client()
                for i in range(3):
                    client.put(SoundCommand('test'))
                client = AvatarStream(api, 'text').create_client().scroll_to_end()
                result = client.pull()
                self.assertEqual(0, len(result))


