from brainbox import BrainBox
from brainbox.utils import TestSpeaker
from unittest import TestCase
from avatar.daemon.stt_service.stt import WhisperRecognitionSetup, RecognitionContext, STTCommand, STTConfirmation
from grammatron import Template, CardinalDub, Utterance



class WhisperIntegrationTestCase(TestCase):
    def dont_test_whisper(self):
        with BrainBox.Api.Test() as api:
            speaker = TestSpeaker(api)
            input = speaker.speak('Set the timer for ten minutes').to_brain_box()

            setup = WhisperRecognitionSetup()
            task = setup.create_task(RecognitionContext(STTCommand(input), {}))
            result = api.execute(task)
            self.assertIsInstance(result, STTConfirmation)
            self.assertEqual('Set the timer for 10 minutes.', result.recognition)

    def dont_test_whisper_with_free_speech(self):
        with BrainBox.Api.Test() as api:
            speaker = TestSpeaker(api)
            input = speaker.speak('Set the timer for ten minutes').to_brain_box()

            template = Template(f"Set the timer for {CardinalDub(11).as_variable('duration')}").with_name('test_template')
            setup = WhisperRecognitionSetup(free_speech_recognition_template=template)
            task = setup.create_task(RecognitionContext(STTCommand(input)))

            result = api.execute(task)
            self.assertIsInstance(result, STTConfirmation)
            self.assertIsInstance(result.recognition, Utterance)
            self.assertEqual('test_template', result.recognition.template.get_name())
            self.assertEqual({'duration': 10}, result.recognition.value)


