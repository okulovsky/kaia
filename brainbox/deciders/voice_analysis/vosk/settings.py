from dataclasses import dataclass
from enum import Enum
from .app.model import VoskModelSpec


class VoskModels(str, Enum):
    en = 'en'
    de = 'de'
    ru = 'ru'


@dataclass
class VoskSettings:

    models_to_install = {
        VoskModels.en: VoskModelSpec('https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip'),
        VoskModels.de: VoskModelSpec('https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip'),
        VoskModels.ru: VoskModelSpec('https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip'),
    }
