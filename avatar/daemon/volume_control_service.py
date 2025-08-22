from typing import *
from dataclasses import dataclass
from ..messaging import IMessage, message_handler
from .common import InitializationEvent, VolumeCommand, AvatarService

@dataclass
class VolumeExternalCommand(IMessage):
    absolute_value: Optional[float] = None
    relative_value: Optional[float] = None
    stash_to: Optional[str] = None
    restore_from: Optional[str] = None




class VolumeControlService(AvatarService):
    Command = VolumeExternalCommand

    def __init__(self, default_value: float = 0.1, initialize_volume: bool = True):
        self.current_value: float | None = None
        self.stash: dict[str, float] = {}
        self.default_value = default_value
        self.initialize_volume = initialize_volume

    def requires_brainbox(self):
        return False

    @message_handler
    def process_volume_command(self, cmd: VolumeExternalCommand) -> VolumeCommand:
        if self.current_value is None:
            self.current_value = self.default_value

        if cmd.stash_to is not None:
            self.stash[cmd.stash_to] = self.current_value

        new_value = None
        if cmd.restore_from is not None and cmd.restore_from in self.stash:
            new_value = self.stash[cmd.restore_from]
        elif cmd.relative_value is not None:
            new_value = self.current_value + cmd.relative_value
        elif cmd.absolute_value is not None:
            new_value = cmd.absolute_value
        if new_value<0:
            new_value = 0
        if new_value>1:
            new_value = 1
        if new_value is not None:
            yield VolumeCommand(new_value)

    @message_handler
    def catch_current_volume(self, cmd: VolumeCommand) -> None:
        self.current_value = cmd.value

    @message_handler
    def initialize(self, cmd: InitializationEvent) -> VolumeCommand|None:
        if self.initialize_volume:
            return VolumeCommand(self.default_value)











