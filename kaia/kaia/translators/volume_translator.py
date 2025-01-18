from typing import *
from dataclasses import dataclass
from eaglesong.core import Translator, TranslatorOutputPackage
from ..server import KaiaApi, Message

@dataclass
class VolumeCommand:
    absolute_value: Optional[float] = None
    relative_value: Optional[float] = None
    stash_to: Optional[str] = None
    restore_from: Optional[str] = None


class VolumeTranslator(Translator):
    def __init__(self,
                 inner_function,
                 volume_callback: Callable[[float], None],
                 default_value: float = 0.1):
        self.volume_callback = volume_callback
        self.stash: Dict[str, float] = {}
        self.current_value = default_value
        super().__init__(inner_function, output_generator_translator=self.process_volume_command)

    def process_volume_command(self, package: TranslatorOutputPackage):
        cmd = package.inner_output
        if not isinstance(cmd, VolumeCommand):
            yield package.inner_output
            return
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
            self.current_value = new_value
            self.volume_callback(new_value)
            yield Message(Message.Type.System, f"Volume set to {int(100*new_value)}%")











