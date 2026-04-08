from brainbox import BrainBox
from avatar.app import AvatarApi

class CharaApis:
    brainbox_api: BrainBox.Api|None = BrainBox.Api('127.0.0.1:8090')
    avatar_api: AvatarApi|None = None
    strict_brainbox_errors: bool = False