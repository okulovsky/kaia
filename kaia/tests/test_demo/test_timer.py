import time
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

            tester.send_voice_command("Set the timer for 10 seconds")
            updates = tester.pull_updates(4)

            tester.send_voice_command("How much timers do I have?")
            updates = tester.pull_updates(5)

            time.sleep(10)
            updates = tester.pull_updates(3)
            updates[1].is_system_message('*alarm ringing*')

