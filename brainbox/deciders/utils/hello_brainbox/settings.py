from dataclasses import dataclass
from ....framework import ConnectionSettings
from .app.model import HelloBrainBoxModelSpec
from enum import Enum

class HelloBrainBoxModels(str, Enum):
    google = 'google'
    facebook = 'facebook'

@dataclass
class HelloBrainBoxSettings:
    connection = ConnectionSettings(20000, 5)
    models_to_install = {
        'google': HelloBrainBoxModelSpec('https://google.com'),
        'facebook': HelloBrainBoxModelSpec('https://facebook.com'),
    }
