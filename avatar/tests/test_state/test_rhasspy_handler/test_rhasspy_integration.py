from avatar.state.rhasspy_utils import RhasspyHandler
from eaglesong.templates import Template, CardinalDub, TemplatesCollection
from unittest import TestCase
from brainbox import BrainBox
from brainbox.deciders import RhasspyKaldi
from avatar.utils import TestSpeaker

class Intents(TemplatesCollection):
    set_timer = Template(f"Set the timer for {CardinalDub(60).as_variable('duration')}")
    cancel_timer = Template(f"Cancel the timer")

class RhasspyIntegrationTestCase(TestCase):
    def test_rhasspy_integration(self):
        intents = Intents.get_templates()
        handler = RhasspyHandler(intents)

        with BrainBox.Api.Test() as api:
            model = 'rhasspy_integration_test_model'
            api.execute(BrainBox.Task.call(RhasspyKaldi).train(model, 'en', handler.ini_file))
            speaker = TestSpeaker(api)

            wav = speaker.speak("Cancel the timer").upload_to_brainbox_with_random_name()
            output = api.execute(BrainBox.Task.call(RhasspyKaldi).transcribe(wav, model))
            result = handler.parse_kaldi_output(output)
            self.assertIn(result, Intents.cancel_timer)

            wav = speaker.speak("Set the timer for thirty-two minutes").upload_to_brainbox_with_random_name()
            output = api.execute(BrainBox.Task.call(RhasspyKaldi).transcribe(wav, model))
            result = handler.parse_kaldi_output(output)
            self.assertIn(result, Intents.set_timer)
            self.assertEqual({'duration': 39}, result.value)



