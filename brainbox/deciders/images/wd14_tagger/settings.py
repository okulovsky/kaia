from dataclasses import dataclass
from ....framework import ConnectionSettings
from .model import WD14TaggerModel

@dataclass
class WD14TaggerSettings:
    connection = ConnectionSettings(20303)
    models_to_download: tuple[WD14TaggerModel,...] = (
        WD14TaggerModel('wd14-vit.v2', 'models--SmilingWolf--wd-v1-4-vit-tagger-v2'),
    )
