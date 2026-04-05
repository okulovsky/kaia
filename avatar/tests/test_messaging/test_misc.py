from avatar.daemon.brainbox_service import BrainBoxServiceCommand
from avatar.app.messages import AvatarMessageRepository
from unittest import TestCase
from brainbox.deciders import Piper

class MiscellaneousTests(TestCase):
    def test_brainbox_command(self):
        cmd = BrainBoxServiceCommand(
            Piper.new_task().voiceover("Test")
        )
        av_message = AvatarMessageRepository._serialize("", cmd)
        print(av_message)