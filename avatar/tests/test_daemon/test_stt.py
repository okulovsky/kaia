from unittest import TestCase
from avatar.daemon import BrainBoxService, STTService, WhisperRecognitionSetup, VoskRecognitionSetup, IntentsPack, RhasspyRecognitionSetup
from avatar.messaging import *
import jsonpickle
from grammatron import Template, TemplatesCollection
from brainbox import BrainBox


def brain_box_mock(task: BrainBox.ITask):
    jobs = task.create_jobs()
    if jobs[-1].decider == 'EmptyDecider':  # It means training
        return 'OK'
    if len(jobs) != 1:
        raise ValueError(
            "Must be either multi-job task for training, or a single-job task for recognition")
    job = jobs[0]
    return jsonpickle.loads(job.arguments['file'])[job.decider]

class STTTestCase(TestCase):
    def test_stt(self):
        proc = AvatarDaemon(TestStream().create_client())
        proc.rules.bind(STTService(WhisperRecognitionSetup()))
        proc.rules.bind(BrainBoxService(brain_box_mock))

        obj=dict(Whisper=STTService.Confirmation('test'))
        proc.client.put(STTService.Command(jsonpickle.dumps(obj)))
        result = proc.debug_and_stop_by_message_type(STTService.Confirmation)

        message = result.messages[-1]
        self.assertIsInstance(message, STTService.Confirmation)
        self.assertEqual('test', message.recognition)


    def test_stt_request(self):
        proc = AvatarDaemon(TestStream().create_client())
        proc.rules.bind(STTService(WhisperRecognitionSetup()))
        proc.rules.bind(BrainBoxService(brain_box_mock))

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
        proc = AvatarDaemon(TestStream().create_client())
        proc.rules.bind(STTService(RhasspyRecognitionSetup('test_1')))
        proc.rules.bind(BrainBoxService(brain_box_mock))

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

        proc = AvatarDaemon(TestStream().create_client())
        stt = STTService(RhasspyRecognitionSetup('test_2'))
        proc.rules.bind(stt)
        proc.rules.bind(BrainBoxService(brain_box_mock))

        obj = dict(RhasspyKaldi=STTService.Confirmation("rhasspy"))
        proc.client.put(STTService.RhasspyTrainingCommand(packs))
        proc.client.put(RhasspyRecognitionSetup('test_2'))
        proc.client.put(STTService.Command(jsonpickle.dumps(obj)))
        messages = proc.debug_and_stop_by_message_type(STTService.Confirmation).messages

        self.assertEqual('rhasspy', messages[-1].recognition)
        bb_command = [m for m in messages if isinstance(m, BrainBoxService.Command)][-1]
        handler = bb_command.task.postprocessor.handler.intent_to_template
        self.assertTrue(list(handler)[0].endswith('Collection2.test_2'))











