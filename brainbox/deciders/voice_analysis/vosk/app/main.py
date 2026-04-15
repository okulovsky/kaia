from foundation_kaia.brainbox_utils import run_brainbox_app, ModelLoadingSupport, ModelInstallingSupport, SingleModelStorage
from model import VoskModelSpec, VoskInstaller
from service import VoskService


if __name__ == '__main__':
    installer = VoskInstaller()
    storage = SingleModelStorage(installer)
    service = VoskService(storage)
    run_brainbox_app([
        service,
        ModelLoadingSupport(storage),
        ModelInstallingSupport[VoskModelSpec](installer),
    ])
