import os

from foundation_kaia.marshalling import Api, TestApi
from .messaging_component import MessagingAPI
from .components import FileCacheApi
from .messaging_component import MessagingComponent
from .server import AvatarServerSettings, AvatarServer
from foundation_kaia.misc import Loc
from ..messaging import Stream


class AvatarApi(Api):
    def __init__(self, address):
        super().__init__(address)

    @property
    def messaging(self):
        return MessagingAPI(self.address)

    @property
    def file_cache(self):
        return FileCacheApi(self.address)

    def create_messaging_stream(self, session: str = 'default') -> Stream:
        from .messaging_component import AvatarStream
        return AvatarStream(self, session)


    class Test(TestApi['AvatarApi']):
        def __init__(self, settings: AvatarServerSettings|None = None):
            self.temp_db_path = None
            if settings is None:
                self.temp_db_path = Loc.temp_folder/'avatar_test_database'
                settings = AvatarServerSettings(
                    (
                        MessagingComponent(self.temp_db_path),
                    )
                )

            super().__init__(lambda z: AvatarApi(z), AvatarServer(settings))

        def __exit__(self, exc_type, exc_val, exc_tb):
            super().__exit__(exc_type, exc_val, exc_tb)
            if self.temp_db_path is not None:
                os.unlink(self.temp_db_path)