from .intents_pack import IntentsPack
from dataclasses import dataclass
from ...common import IMessage
from .rhasspy_handler import RhasspyHandler

@dataclass
class RhasspyTrainCommand(IMessage):
    intents_packs: tuple[IntentsPack, ...]

@dataclass
class RhasspyTrainConfirmation(IMessage):
    pass


class RhasspyTrainer:
    def __init__(self):
        name_to_handler: dict[str, RhasspyHandler]|None = None

    def train(self, message: RhasspyTrainCommand):
        