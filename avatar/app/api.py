import requests as _requests

from foundation_kaia.marshalling import ApiUtils, StorageApi, TestApi, StorageApiWrap, IStorage
from .messages import AvatarMessagingApi, AvatarMessageRepository
from ..messaging import AvatarClient
from brainbox.framework.common.streaming import StreamingStorageApi
from pathlib import Path


class AvatarApi:
    def __init__(self, base_url: str):
        self.base_url=base_url
        self.cache = StorageApi(base_url, 'cache')
        self.messages = AvatarMessagingApi(base_url)
        self.streaming = StreamingStorageApi(base_url, 'streaming')
        self._resources_storage = StorageApi(base_url, 'resources')

    def resources(self, service: str|type) -> IStorage:
        if isinstance(service, str):
            name = service
        elif isinstance(service, type):
            name = service.__name__.split('.')[-1]
        else:
            raise ValueError("Expected str or type")
        return StorageApiWrap(self._resources_storage, name)


    def create_client(self, session: str|None = None):
        repo = AvatarMessageRepository(self.messages)
        return AvatarClient(repo, 'default' if session is None else session)


    def audio_dashboard_snapshot(self) -> bytes:
        r = _requests.get(f'{self.base_url}/audio_dashboard/snapshot')
        r.raise_for_status()
        return r.content

    def wait_for_connection(self, time_in_seconds: int = 10) -> None:
        ApiUtils.wait_for_reply(f'{self.base_url}/heartbeat', time_in_seconds)

    @staticmethod
    def test(folder: Path|None = None) -> 'TestApi[AvatarApi]':
        from .server import AvatarServer, AvatarServerSettings
        settings = AvatarServerSettings()
        if folder is not None:
            settings.cache_folder = folder/'cache'
            settings.resources_folder = folder/'resources'

        return TestApi(AvatarApi, AvatarServer(settings))