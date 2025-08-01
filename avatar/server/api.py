from foundation_kaia.marshalling import Api, TestApi
from .messaging_api import MessagingAPI
from .components import FileCacheApi
from .server import AvatarServerSettings, AvatarServer

class AvatarApi(Api):
    def __init__(self, address):
        super().__init__(address)

    @property
    def messaging(self):
        return MessagingAPI(self.address)

    @property
    def file_cache(self):
        return FileCacheApi(self.address)

    class Test(TestApi['AvatarApi']):
        def __init__(self, settings: AvatarServerSettings):
            super().__init__(lambda z: AvatarApi(z), AvatarServer(settings))