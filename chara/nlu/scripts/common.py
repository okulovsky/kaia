from pathlib import Path
from chara.common import Chara


def default_ultimate_nlu_folder() -> Path:
    return Chara.Apis.content_folder/'nlu'/'ultimate-nlu'
