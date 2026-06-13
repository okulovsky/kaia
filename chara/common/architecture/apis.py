from brainbox import BrainBox
from avatar.app import AvatarApi
from foundation_kaia.misc import Loc
from pathlib import Path
from dataclasses import dataclass
import os

@dataclass
class CharaApis:
    brainbox_api: BrainBox.Api
    avatar_api: AvatarApi
    content_folder: Path
    cache_folder: Path

    @staticmethod
    def default() -> 'CharaApis':
        brainbox_url = os.environ.get('CHARA_BRAINBOX_URL', 'http://127.0.0.1:8090')
        avatar_url = os.environ.get('CHARA_AVATAR_URL', 'http://127.0.0.1:13000')
        content_folder = Path(os.environ.get('CHARA_CONTENT_FOLDER', Loc.data_folder))
        cache_folder = Path(os.environ.get('CHARA_CACHE_FOLDER', Loc.temp_folder/'chara-pipelines'))
        return CharaApis(
            BrainBox.Api(brainbox_url),
            AvatarApi(avatar_url),
            content_folder,
            cache_folder,
        )
