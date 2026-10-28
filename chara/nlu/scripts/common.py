import hashlib
from pathlib import Path
from chara.common import Chara


def default_ultimate_nlu_folder() -> Path:
    return Chara.Apis.content_folder/'nlu'/'ultimate-nlu'


def read_negatives(folder: Path) -> list[str]:
    """The phrases of `folder`/negatives.txt that are not commands, see create_negatives; empty if there is no file"""
    path = folder/'negatives.txt'
    if not path.is_file():
        return []
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def training_folder(folder: Path) -> Path:
    """The Chara folder of the training on the current `folder`/dataset.json and `folder`/negatives.txt"""
    content = (folder/'dataset.json').read_bytes() + '\n'.join(read_negatives(folder)).encode('utf-8')
    fingerprint = hashlib.sha256(content).hexdigest()[:16]
    return folder/'$training'/fingerprint
