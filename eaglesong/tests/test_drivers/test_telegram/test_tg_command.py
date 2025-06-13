from eaglesong.drivers.telegram import TgCommand
from unittest import TestCase

class TgCommandMockTestCase(TestCase):
    def test_mock(self):
        cmd = TgCommand.mock().send_message(text='test', reply_to_message_id=123) #type: TgCommand
        self.assertEqual('send_message', cmd.bot_method)
        self.assertDictEqual({'text': 'test', 'reply_to_message_id': 123}, cmd.kwargs)