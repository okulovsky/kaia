import hashlib
from pathlib import Path
from chara.common import Chara


def default_ultimate_nlu_folder() -> Path:
    return Chara.Apis.content_folder/'nlu'/'ultimate-nlu'


def training_folder(folder: Path) -> Path:
    """The Chara folder of the training on the current `folder`/dataset.json"""
    fingerprint = hashlib.sha256((folder/'dataset.json').read_bytes()).hexdigest()[:16]
    return folder/'$training'/fingerprint
