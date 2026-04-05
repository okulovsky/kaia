from brainbox.framework import ConnectionSettings
from .app.installer import PiperTrainingModel
from dataclasses import dataclass

class PiperTrainingModels:
    lessac = 'lessac'
    denis = 'denis'
    thorsten = 'thorsten'

@dataclass
class PiperTrainingSettings:
    connection = ConnectionSettings(20206, 20)
    models_to_install = {
        PiperTrainingModels.lessac: PiperTrainingModel(
            'https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/en/en_US/lessac/medium/epoch%3D2164-step%3D1355540.ckpt?download=true',
            2164,
            'en-us',
        ),
        PiperTrainingModels.denis: PiperTrainingModel(
            'https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/ru/ru_RU/denis/medium/epoch%3D4474-step%3D1521860.ckpt?download=true',
            4474,
            'ru',
        ),
        PiperTrainingModels.thorsten: PiperTrainingModel(
            'https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/de/de_DE/thorsten/medium/epoch%3D3135-step%3D2702056.ckpt?download=true',
            3135,
            'de'
        )
    }