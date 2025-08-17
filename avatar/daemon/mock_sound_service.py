from .common.known_messages import SoundCommand, SoundConfirmation, PlayableTextMessage
from .common import AvatarService, message_handler, Confirmation


class MockSoundService(AvatarService):
    @message_handler
    def handle_sound(self, message: SoundCommand) -> SoundConfirmation:
        return SoundConfirmation().as_confirmation_for(message)

    def requires_brainbox(self):
        return False


class MockVoiceoverService(AvatarService):
    @message_handler
    def handle_playable(self, message: PlayableTextMessage) -> Confirmation:
        return message.confirm_this()

    def requires_brainbox(self):
        return False