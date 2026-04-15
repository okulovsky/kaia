from ...marshalling import service, endpoint
from .installer import Installer

@service
class IInstallingSupport:
    @endpoint
    def install(self) -> None:
        ...


class InstallingSupport(IInstallingSupport):
    def __init__(self, installer: Installer):
        self.installer = installer

    def install(self) -> None:
        self.installer.install_service()