from unittest import TestCase
from kaia.common import Loc
from kaia.demo import *
from kaia.demo.avatar import characters


class WihoutAudioTestCase(TestCase):
    def test_without_audio(self):
        with Loc.create_test_folder() as folder:
            app = KaiaApp(folder)
            set_brainbox_service_and_api(app)
            set_avatar_service_and_api(app)
            set_web_service_and_api(app)
            set_core_service(app)

            with KaiaAppTester(app, self) as tester:

                tester.send_initial_package()
                updates = tester.pull_updates(7)
                updates[0].of_type('command_initialize')
                updates[1].is_system_message('Rhasspy')
                updates[2].is_system_message('Rhasspy')
                updates[3].is_image()
                updates[4].is_bot_message("Hello")
                updates[5].is_bot_audio("Hello!")
                updates[6].is_bot_audio("Nice to see you!")

                tester.send_voice_command("How are you?")
                updates = tester.pull_updates(4)
                updates[0].of_type('command_audio')
                updates[1].is_user_message('Are you here?')
                updates[2].is_bot_message("Sure, I'm listening")
                updates[3].is_bot_audio("Sure, I'm listening")

                for character in characters:
                    tester.send_voice_command(f"I want to talk with {character}")
                    updates = tester.pull_updates(6)
                    updates[0].of_type('command_audio')
                    updates[1].is_user_message(f'I want to talk with {character}')
                    updates[2].is_image(character)
                    updates[3].is_bot_message('Hello! Nice to see you!', character)
                    updates[4].is_bot_audio('Hello!', character)
                    updates[5].is_bot_audio('Nice to see you!', character)









