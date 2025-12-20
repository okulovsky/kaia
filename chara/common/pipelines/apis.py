from brainbox import BrainBox
from avatar.server import AvatarApi

class CharaApis:
    brainbox_api: BrainBox.Api|None = None
    avatar_api: AvatarApi|None = None