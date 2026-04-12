import os

from .common import AvatarService, SoundLevelReport, InitializationEvent, SetSilenceLevelCommand
from ..messaging import message_handler
from pathlib import Path


class SilenceLevelService(AvatarService):
    def __init__(self,
                 default_silence_level: float = 0.1
                 ):
        self.default_silence_level = default_silence_level
        self.current_silence_level = None

    def requires_brainbox(self):
        return False

    def get_settings_file(self) -> Path:
        return self.resources_folder / 'silence_level.txt'

    def _write_file(self, value):
        os.makedirs(self.get_settings_file().parent, exist_ok=True)
        self.get_settings_file().write_text(str(self.current_silence_level))

    @message_handler
    def on_initialization(self, message: InitializationEvent) -> SetSilenceLevelCommand:
        path = self.get_settings_file()
        if path.is_file():
            value = float(path.read_text())
        else:
            value = self.default_silence_level
            self._write_file(value)
        return SetSilenceLevelCommand(value)

    @message_handler
    def on_changed_level(self, message: SoundLevelReport) -> None:
        if self.current_silence_level != message.silence_level:
            self.current_silence_level = message.silence_level
            self._write_file(message.silence_level)


