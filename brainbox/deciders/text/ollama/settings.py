from dataclasses import dataclass
from ....framework import ConnectionSettings


@dataclass
class OllamaSettings:
    connection = ConnectionSettings(20401)
    models_to_install: tuple[str, ...] = ('llama3.2:1b',)
