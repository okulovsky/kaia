from unittest import TestCase
from avatar.services import BrainBoxService, STTService, WhisperRecognitionSetup, VoskRecognitionSetup, IntentsPack, RhasspyRecognitionSetup
from avatar.messaging import *
import jsonpickle
from grammatron import Template, TemplatesCollection


class STTTestCase(TestCase):
    def test_stt(self):
        proc = AvatarProcessor(TestStream().create_client())
        proc.rules.bind(STTService(WhisperRecognitionSetup()))
        proc.rules.bind(BrainBoxService(STTService.brain_box_mock))

        obj=dict(Whisper=STTService.Confirmation('test'))
        proc.client.put(STTService.Command(jsonpickle.dumps(obj)))
        result = proc.debug_and_stop_by_message_type(STTService.Confirmation)

        message = result.messages[-1]
        self.assertIsInstance(message, STTService.Confirmation)
        self.assertEqual('test', message.recognition)



    def test_stt_request(self):
        proc = AvatarProcessor(TestStream().create_client())
        proc.rules.bind(STTService(WhisperRecognitionSetup()))
        proc.rules.bind(BrainBoxService(STTService.brain_box_mock))

        obj1 = dict(Vosk = STTService.Confirmation("vosk"))
        proc.client.put(VoskRecognitionSetup('x'))
        proc.client.put(STTService.Command(jsonpickle.dumps(obj1)))

        message_1 = proc.debug_and_stop_by_message_type(STTService.Confirmation).messages[-1]

        self.assertEqual('vosk', message_1.recognition)

        obj2 = dict(Whisper=STTService.Confirmation("whisper"))
        proc.client.put(STTService.Command(jsonpickle.dumps(obj2)))

        message_2 = proc.debug_and_stop_by_message_type(STTService.Confirmation).messages[-1]
        self.assertEqual('whisper', message_2.recognition)

    def test_stt_kaldi_no_training(self):
        proc = AvatarProcessor(TestStream().create_client())
        proc.rules.bind(STTService(RhasspyRecognitionSetup('test_1')))
        proc.rules.bind(BrainBoxService(STTService.brain_box_mock))

        obj = dict(RhasspyKaldi=STTService.Confirmation("rhasspy"))
        proc.client.put(STTService.Command(jsonpickle.dumps(obj)))
        self.assertRaises(ValueError, lambda: proc.debug_and_stop_by_message_type(STTService.Confirmation))

    def test_stt_kaldi_trainig(self):
        class Collection1(TemplatesCollection):
            test_1 = Template("Test one")
        class Collection2(TemplatesCollection):
            test_2 = Template("Test two")

        packs = [
            IntentsPack('test_1', tuple(Collection1.get_templates()), {}, 'en'),
            IntentsPack('test_2', tuple(Collection2.get_templates()), {}, 'en')
        ]

        proc = AvatarProcessor(TestStream().create_client())
        stt = STTService(RhasspyRecognitionSetup('test_2'))
        proc.rules.bind(stt)
        proc.rules.bind(BrainBoxService(STTService.brain_box_mock))

        obj = dict(RhasspyKaldi=STTService.Confirmation("rhasspy"))
        proc.client.put(STTService.RhasspyTrainingCommand(packs))
        proc.client.put(RhasspyRecognitionSetup('test_2'))
        proc.client.put(STTService.Command(jsonpickle.dumps(obj)))
        messages = proc.debug_and_stop_by_message_type(STTService.Confirmation).messages

        self.assertEqual('rhasspy', messages[-1].recognition)
        bb_command = [m for m in messages if isinstance(m, BrainBoxService.Command)][-1]
        handler = bb_command.task.postprocessor.handler.intent_to_template
        self.assertTrue(list(handler)[0].endswith('Collection2.test_2'))











