import time
from unittest import TestCase
from kaia.common import Loc
from kaia.demo import *
from kaia.kaia import audio_control as ac
from kaia.tests.test_kaia.test_audio_control import create_test_settings



class WithAudioTestCase(TestCase):
    def test_with_audio(self):
        with Loc.create_test_folder() as folder:
            app = KaiaApp(folder)
            set_brainbox_service_and_api(app)
            set_streaming_service_and_api_address(app)
            set_avatar_service_and_api(app)
            set_web_service_and_api(app)

            settings = create_test_settings(
                app.wav_streaming_api,
                ApiCallback(f'127.0.0.1:{app.kaia_server.settings.port}', app.session_id)
            )

            app.audio_control_server = ac.AudioControlServer(ac.AudioControlService(settings.create_audio_control), settings.port)
            app.audio_control_api = ac.AudioControlApi(f'127.0.0.1:{settings.port}')
            set_core_service(app)

            with KaiaAppTester(app, self) as tester:

                tester.send_initial_package()
                updates = tester.pull_updates(7)
                updates[-1].is_bot_audio()
                updates[-2].is_bot_audio()

                #Because AC is disabled when sounds are playing
                self.assertEqual(ac.MicState.Disabled, app.audio_control_api.get_state())
                tester.send_sound_confirmation(updates[-2])
                self.assertEqual(ac.MicState.Disabled, app.audio_control_api.get_state())
                tester.send_sound_confirmation(updates[-1])
                time.sleep(0.1)
                self.assertEqual(ac.MicState.Standby, app.audio_control_api.get_state())
                tester.pull_updates(2)

                #Simple skill, doesn't open mic in the end
                tester.send_voice_command_via_audio_control('Computer')
                self.assertEqual(ac.MicState.Open, app.audio_control_api.get_state())
                tester.send_voice_command_via_audio_control("Are you here?")
                updates = tester.pull_updates(4)
                updates[1].is_user_message("Are you here?")
                updates[2].is_bot_message("Sure, I'm listening")
                self.assertEqual(ac.MicState.Disabled, app.audio_control_api.get_state())
                tester.send_sound_confirmation(updates[-1])
                time.sleep(0.1)
                self.assertEqual(ac.MicState.Standby, app.audio_control_api.get_state())
                tester.pull_updates(1)

                tester.send_voice_command_via_audio_control("Computer")
                self.assertEqual(ac.MicState.Open, app.audio_control_api.get_state())
                tester.send_voice_command_via_audio_control("Repeat after me!")
                updates = tester.pull_updates(4)
                updates[1].is_user_message("Repeat after me!")
                updates[2].is_bot_message("Say anything and I will repeat")
                self.assertEqual(ac.MicState.Disabled, app.audio_control_api.get_state())
                tester.send_sound_confirmation(updates[-1])
                time.sleep(0.1)
                self.assertEqual(ac.MicState.Open, app.audio_control_api.get_state()) #Because the mic was opened by the skill
                tester.pull_updates(1)

                tester.send_voice_command_via_audio_control("Happy New Year!")
                updates = tester.pull_updates(4)
                updates[1].is_user_message('Happy New Year!')
                updates[2].is_bot_message('Happy New Year!')
                self.assertEqual(ac.MicState.Disabled, app.audio_control_api.get_state())
                tester.send_sound_confirmation(updates[-1])
                time.sleep(0.1)
                self.assertEqual(ac.MicState.Standby, app.audio_control_api.get_state())





