from dataclasses import dataclass
from ....framework import ConnectionSettings
from .model import VoskModel

@dataclass
class VoskSettings:
    connection = ConnectionSettings(20105, 20)

    models_to_download = (
        VoskModel(
            'en',
            'https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip'
        ),
        VoskModel(
            'de',
            'https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip'
        )
    )
