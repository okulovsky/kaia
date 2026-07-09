from ..common import AvatarService, message_handler
from .music_player import IMusicPlayer
from .commands import *
from ...messaging import TickEvent


class MusicService(AvatarService):
    def __init__(self, player: IMusicPlayer):
        self.player = player
        self.has_music = False

    @message_handler
    def on_start(self, command: MusicStartCommand):
        self.has_music = True
        self.player.start(command.id)

    @message_handler
    def on_tick(self, command: TickEvent):
        if not self.has_music:
            return MusicStatusCommand(MusicStatus(False, False, None))
        try:
            status = self.player.status()
        except Exception:
            self.has_music = False
            try:
                self.player.stop()
            except Exception:
                pass
            return MusicStatusCommand(MusicStatus(False, False, None))
        return MusicStatusCommand(status)

    @message_handler
    def on_stop(self, command: MusicStopButtonEvent):
        self.has_music = False
        self.player.stop()

    @message_handler
    def on_pause(self, command: MusicPauseButtonEvent):
        self.player.pause()

    @message_handler
    def on_resume(self, command: MusicResumeButtonEvent):
        self.player.resume()

    @message_handler
    def on_previous(self, command: MusicPreviousButtonEvent):
        self.player.previous()

    @message_handler
    def on_next(self, command: MusicNextButtonEvent):
        self.player.next()

    def requires_brainbox(self):
        return False