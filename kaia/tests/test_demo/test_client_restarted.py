from unittest import TestCase
from kaia.common import Loc
from kaia.tests.test_demo.setup import TestSetup


class RestartsTestCase(TestCase):
    def test_client_restarted(self):
        with TestSetup(self) as tester:
            #Start normally
            tester.send_initial_package()
            updates = tester.pull_updates(8)
            updates[4].is_image()
            tester.send_voice_command("How are you?")
            updates = tester.pull_updates(4)

            #Now client suddenly restarts
            last_id = tester.send_initial_package()['id']
            updates = tester.pull_updates_via_html(last_id, 4)
            updates[0].is_image()
            updates[1].is_bot_message('Hello! Nice to see you!')
            updates[2].is_bot_audio('Hello!')
            updates[3].is_bot_audio('Nice to see you!')



