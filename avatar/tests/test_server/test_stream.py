from avatar.daemon import SoundCommand, TextEvent
from avatar.server import AvatarApi, AvatarStream
from unittest import TestCase
from foundation_kaia.misc import Loc

class AvatarStreamTestCase(TestCase):
    def test_stream(self):
        with AvatarApi.Test() as api:
            client = AvatarStream(api, 'test').create_client()
            client.put(SoundCommand('test'))
            messages = client.pull()
            self.assertIsInstance(messages[0], SoundCommand)

    def test_stream_scroll_down(self):
        with AvatarApi.Test() as api:
            client = AvatarStream(api, 'test').create_client()
            for i in range(3):
                client.put(SoundCommand('test'))
            client = AvatarStream(api, 'test').create_client().scroll_to_end()
            result = client.pull()
            self.assertEqual(0, len(result))


    def test_stream_counted(self):
        with AvatarApi.Test() as api:
            client = AvatarStream(api, 'test').create_client()
            for i in range(5):
                client.put(TextEvent(str(i)))
            data = client.pull(2)
            self.assertEqual(2, len(data))
            self.assertEqual('0', data[0].text)
            self.assertEqual('1', data[1].text)

    def test_stream_counted_from_tail(self):
        with AvatarApi.Test() as api:
            client = AvatarStream(api, 'test').create_client()
            for i in range(5):
                client.put(TextEvent(str(i)))
            data = client.pull_tail(2)
            self.assertEqual(2, len(data))
            self.assertEqual('3', data[0].text)
            self.assertEqual('4', data[1].text)
            self.assertEqual(0, len(client.pull()))

    def test_stream_types(self):
        with AvatarApi.Test() as api:
            client = AvatarStream(api, 'test').create_client()
            for i in range(5):
                client.put(SoundCommand(str(i)))
                client.put(TextEvent(str(i)))
            data = client.with_types(TextEvent).pull()
            self.assertEqual(5, len(data))









