from unittest import TestCase
from avatar.messaging import Confirmation, Envelop
from avatar.server.serialization import from_json, to_json
from avatar.services import PlayableTextMessage, TextEvent, TextInfo, ButtonGrid
from pprint import pprint

class SpecialCasesSerializationTestCase(TestCase):
    def test_confirmation(self):
        result = from_json({}, Confirmation)
        self.assertIsNone(result.error)

    def test_tuple(self):
        env: Envelop = from_json({'confirmation_for': ['123']}, Envelop)
        self.assertEquals(('123',), env.confirmation_for)

    def test_playable_text(self):
        msg = PlayableTextMessage(TextEvent('test'), TextInfo('speaker', 'en'))
        result = to_json(msg, PlayableTextMessage)
        self.assertIn('py/object', result['text'])
        self.assertNotIn('py/object', result['info'])

    def test_button_grid(self):
        msg = ButtonGrid.Builder().add('test1','test1').add('test2', 'test2').to_grid()
        result = to_json(msg, ButtonGrid)
        self.assertIsInstance(result['elements'], list)
        self.assertIn('py/object', result['elements'][0])

        deserialized = from_json(result, ButtonGrid)
        pprint(deserialized)


