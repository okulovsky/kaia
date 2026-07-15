from dataclasses import dataclass
from enum import Enum


class WD14TaggerModels(str, Enum):
    wd14_vit_v2 = 'wd14-vit.v2'


@dataclass
class WD14TaggerSettings:
    models_to_install = [WD14TaggerModels.wd14_vit_v2]
    cpu_share: float = 0.25
