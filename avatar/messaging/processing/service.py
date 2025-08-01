from ..stream import StreamClient

class IService:
    def set_client(self, client: StreamClient):
        self._client = client

    @property
    def client(self) -> StreamClient:
        return self._client
