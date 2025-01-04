from unittest import TestCase
from kaia.demo import KaiaAppTester
from kaia.demo.avatar import characters
from kaia.tests.test_demo.setup import TestSetup


class WihoutAudioTestCase(TestCase):
    def test_without_audio(self):
        with TestSetup(self) as tester:
            updates = tester.pull_updates(3)
            updates[0].is_system_message('Rhasspy')
            updates[1].is_system_message('Rhasspy')
            updates[2].of_type('notification_driver_start')

            tester.send_initial_package()
            updates = tester.pull_updates(5)
            updates[0].of_type('command_initialize')
            updates[1].is_image()
            updates[2].is_bot_message("Hello")
            updates[3].is_bot_audio("Hello!")
            updates[4].is_bot_audio("Nice to see you!")

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


    def test_initialization_if_request_comes_too_early(self):
        with TestSetup(self) as tester:
            tester.send_initial_package()
            updates = tester.pull_updates(8)
            updates[0].of_type('command_initialize')
            updates[1].is_system_message('Rhasspy')
            updates[2].is_system_message('Rhasspy')
            updates[3].of_type('notification_driver_start')
            updates[4].is_image()
            updates[5].is_bot_message("Hello")
            updates[6].is_bot_audio("Hello!")
            updates[7].is_bot_audio("Nice to see you!")






