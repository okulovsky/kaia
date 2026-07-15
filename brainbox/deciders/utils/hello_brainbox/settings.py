from dataclasses import dataclass
from .app.model import HelloBrainBoxModelSpec
from enum import Enum

class HelloBrainBoxModels(str, Enum):
    google = 'google'
    facebook = 'facebook'

@dataclass
class HelloBrainBoxSettings:
    models_to_install = {
        'google': HelloBrainBoxModelSpec('https://google.com'),
        'facebook': HelloBrainBoxModelSpec('https://facebook.com'),
    }
