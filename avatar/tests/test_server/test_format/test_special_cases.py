from unittest import TestCase
from avatar.messaging import Confirmation, Envelop
from avatar.server.messaging_component.format import Format
from avatar.daemon import PlayableTextMessage, TextEvent, TextInfo, ButtonGridCommand, IntentsPack, STTService, BrainBoxService
from pprint import pprint
from brainbox.deciders import Empty
from brainbox import BrainBox
import json

class SpecialCasesSerializationTestCase(TestCase):
    def test_confirmation(self):
        result = Format.from_json({}, Confirmation)
        self.assertIsNone(result.error)

    def test_tuple(self):
        env: Envelop = Format.from_json({'confirmation_for': ['123'], 'id' : 'x'}, Envelop)
        self.assertEqual(('123',), env.confirmation_for)

    def test_datetime(self):
        msg = Envelop()
        js = Format.to_json(msg, Envelop)
        self.assertNotIn('@base64', json.dumps(js))

    def test_playable_text(self):
        msg = PlayableTextMessage(TextEvent('test'), TextInfo('speaker', 'en'))
        result = Format.to_json(msg, PlayableTextMessage)
        self.assertIn('@base64', result['text'])
        self.assertNotIn('@base64', result['info'])



    def test_button_grid(self):
        msg = ButtonGridCommand.Builder().add('test1','test1').add('test2', 'test2').to_grid()
        result = Format.to_json(msg, ButtonGridCommand)
        self.assertIsInstance(result['elements'], list)
        self.assertNotIn('@base64', result['elements'][0])

    def test_intents_pack(self):
        pack = IntentsPack('test', (), {}, 'en')
        msg = STTService.RhasspyTrainingCommand([pack])
        result: STTService.RhasspyTrainingCommand = Format.from_json(Format.to_json(msg, STTService.RhasspyTrainingCommand), STTService.RhasspyTrainingCommand)
        self.assertIsInstance(result.intent_packs[0], IntentsPack)

    def test_brainbox_command(self):
        msg = BrainBoxService.Command(BrainBox.Task.call(Empty)())
        js = Format.to_json(msg, BrainBoxService.Command)
        fr = Format.from_json(js, BrainBoxService.Command)
        print(fr)



