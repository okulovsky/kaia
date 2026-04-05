from dataclasses import dataclass
from enum import Enum
from ....framework import ConnectionSettings
from .app.model import InsightFaceModelSpec


class InsightFaceModels(str, Enum):
    buffalo_l = 'buffalo_l'


@dataclass
class InsightFaceSettings:
    connection = ConnectionSettings(20304)

    models_to_install = {
        InsightFaceModels.buffalo_l: InsightFaceModelSpec(det_size=(320, 320)),
    }
