from brainbox.framework import ConnectionSettings
from dataclasses import dataclass


@dataclass
class OneTrainerSettings:
    connection = ConnectionSettings(20306)
