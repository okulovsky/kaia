from kaia.kaia import audio_control as ac
from unittest import TestCase
from kaia.tests.test_kaia.test_audio_control import create_test_settings

class StateChangeTestCase(TestCase):
    def test_state_change(self):
        settings = create_test_settings(None, None)
        with ac.AudioControlApi.Test(settings.create_audio_control, settings.port) as api:
            self.assertEqual(ac.MicState.Standby, api.get_state())
            api.set_state(ac.MicState.Disabled)
            self.assertEqual(ac.MicState.Disabled, api.get_state())
            api.set_state(ac.MicState.Standby)
            self.assertEqual(ac.MicState.Standby, api.get_state())

