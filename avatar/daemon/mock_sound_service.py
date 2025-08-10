from .common.known_messages import SoundCommand, SoundConfirmation
from .common import AvatarService, message_handler

class MockSoundService(AvatarService):
    @message_handler
    def handle_sound(self, message: SoundCommand):
        return SoundConfirmation().as_confirmation_for(message)

    def requires_brainbox(self):
        return True
