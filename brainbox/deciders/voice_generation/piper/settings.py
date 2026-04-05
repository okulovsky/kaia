from dataclasses import dataclass
from enum import Enum
from ....framework import ConnectionSettings
from .app.model import PiperModelSpec


class PiperModels(str, Enum):
    en = 'en'
    ru = 'ru'
    de = 'de'


@dataclass
class PiperSettings:
    connection = ConnectionSettings(20205)
    models_to_install = {
        'en': PiperModelSpec(
            config_url="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json?download=true",
            url="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alba/medium/en_GB-alba-medium.onnx"
        ),
        'ru': PiperModelSpec(
            config_url='https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.onnx.json?download=true',
            url='https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.onnx?download=true'
        ),
        'de': PiperModelSpec(
            config_url="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json?download=true",
            url="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx?download=true"
        ),
    }
