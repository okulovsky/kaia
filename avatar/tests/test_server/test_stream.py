from avatar.services import SoundCommand, UtteranceEvent, PlayableTextMessage, TextInfo, TextEvent
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
                client = AvatarStream(api.messaging, 'test').create_client()
                client.put(SoundCommand('test'))
                messages = client.pull()
                self.assertIsInstance(messages[0], SoundCommand)


