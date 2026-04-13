from foundation_kaia.brainbox_utils import Installer
from ..architecture import TSettings
from ..docker_web_service_controller import DockerWebServiceController
from foundation_kaia.marshalling import DeclaredType
from typing import Generic

class DockerMarshallingController(DockerWebServiceController, Generic[TSettings]):
    def get_default_settings(self) -> TSettings:
        settings_type = DeclaredType.parse(self).find_type(DockerMarshallingController).type_map[TSettings]
        return settings_type()

    def get_installer(self) -> Installer|None:
        return None

    def get_notebook_configuration(self) -> dict:
        return self.get_service_run_configuration(None).as_service_worker('--notebook')

    def post_install(self):
        from .post_install_process import PostInstallProcess
        PostInstallProcess(self)()
