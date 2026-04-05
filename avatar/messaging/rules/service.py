from ..core import AvatarClient
from .binding_settings import BindingSettings
from pathlib import Path

class IService:
    def set_client(self, client: AvatarClient):
        self._client = client

    def set_resources_folder(self, folder: Path):
        self._resources_folder = folder


    @property
    def client(self) -> AvatarClient:
        return self._client

    @property
    def resources_folder(self) -> Path:
        if not hasattr(self, '_resources_folder'):
            return None
        return self._resources_folder

    @property
    def binding_settings(self):
        if not hasattr(self,'_binding_settings'):
            self._binding_settings = BindingSettings()
        return self._binding_settings