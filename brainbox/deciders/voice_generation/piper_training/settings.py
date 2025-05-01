from dataclasses import dataclass
from .model import PiperTrainingModel

@dataclass
class PiperTrainingSettings:
    models_to_download: tuple[PiperTrainingModel,...] = (
        PiperTrainingModel(
            'lessac.ckpt',
            'https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/en/en_US/lessac/medium/epoch%3D2164-step%3D1355540.ckpt?download=true'
        ),
    )