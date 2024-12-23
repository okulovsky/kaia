from dataclasses import dataclass
from ....framework import ConnectionSettings

@dataclass
class WhisperSettings:
    connection: ConnectionSettings = ConnectionSettings(20102, 15)

    models_to_download: tuple[str,...] = (
        'base',
    )


