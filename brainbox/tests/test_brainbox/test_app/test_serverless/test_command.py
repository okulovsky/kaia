from unittest import TestCase
from brainbox import BrainBoxCommand, BrainBox
from brainbox.deciders import FakeText
from brainbox.framework.common import Loc

class BrainBoxCommandTestCase(TestCase):
    def test_command_without_cache(self):
        with BrainBox.Api.ServerlessTest([FakeText]) as api:
            command = BrainBoxCommand[str](BrainBox.Task.call(FakeText)())
            result = command.execute(api)
            self.assertIsInstance(result, str)

            command = BrainBoxCommand[str](BrainBox.Task.call(FakeText)())
            command.add(api)
            result = command.join(api)
            self.assertIsInstance(result, str)


    def test_command_with_cache(self):
        with Loc.create_test_file('json') as filename:
            with BrainBox.Api.ServerlessTest([FakeText]) as api:
                command = BrainBoxCommand[str](BrainBox.Task.call(FakeText)()).with_cache(filename)
                command.execute(api)
                command.execute(api)
                self.assertEqual(1, len(api.summary()))

                command.add(api)
                self.assertEqual(1, len(api.summary()))

                command.join(api)
                self.assertEqual(1, len(api.summary()))








