from dataclasses import dataclass
from ....framework import ConnectionSettings
from .model import OllamaModel

@dataclass
class OllamaSettings:
    connection = ConnectionSettings(20401)
    models_to_install: tuple[OllamaModel,...] = (
        OllamaModel('llama3.2:1b'),
    )
