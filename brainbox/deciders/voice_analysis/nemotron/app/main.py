from foundation_kaia.brainbox_utils import run_brainbox_app, ModelLoadingSupport, ModelInstallingSupport, SingleModelStorage
from model import NemotronModelSpec, NemotronInstaller
from service import NemotronService


if __name__ == '__main__':
    installer = NemotronInstaller()
    storage = SingleModelStorage(installer)
    service = NemotronService(storage)
    run_brainbox_app([
        service,
        ModelLoadingSupport(storage),
        ModelInstallingSupport[NemotronModelSpec](installer),
    ])
