from ..stream import StreamClient
from .binding_settings import BindingSettings

class IService:
    def set_client(self, client: StreamClient):
        self._client = client

    @property
    def client(self) -> StreamClient:
        return self._client

    @property
    def binding_settings(self):
        if not hasattr(self,'_binding_settings'):
            self._binding_settings = BindingSettings()
        return self._binding_settings