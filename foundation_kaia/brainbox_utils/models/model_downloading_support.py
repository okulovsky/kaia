from typing import Generic

from ...marshalling_2 import service, endpoint
from .installer import Installer, TModelSpec
from .installing_support import IInstallingSupport, InstallingSupport

@service
class IModelInstallingSupport(IInstallingSupport, Generic[TModelSpec]):
    @endpoint(force_json_params=True)
    def download_model(self, model: str, model_spec: TModelSpec) -> None:
        ...


class ModelInstallingSupport(InstallingSupport, IModelInstallingSupport[TModelSpec]):
    def __init__(self, installer: Installer[TModelSpec]):
        super().__init__(installer)

    def download_model(self, model: str, model_spec: TModelSpec) -> None:
        self.installer.download_model(model, model_spec)
