from .service import AvatarSettings, AvatarService
from foundation_kaia.marshalling import Server

class AvatarServer(Server):
    def __init__(self, settings: AvatarSettings):
        super().__init__(settings.port, AvatarService(settings))
