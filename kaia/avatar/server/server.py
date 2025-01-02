from .service import AvatarSettings, AvatarService
from brainbox.framework.common.marshalling import Server

class AvatarServer(Server):
    def __init__(self, settings: AvatarSettings):
        super().__init__(settings.port, AvatarService(settings))
