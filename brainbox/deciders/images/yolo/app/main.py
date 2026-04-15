from foundation_kaia.brainbox_utils import run_brainbox_app, SingleModelStorage, ModelLoadingSupport, ModelInstallingSupport
from model import YoloInstaller
from service import YoloService


if __name__ == '__main__':
    installer = YoloInstaller()
    storage = SingleModelStorage(installer)
    service = YoloService(storage)
    run_brainbox_app([
        service,
        ModelLoadingSupport(storage),
        ModelInstallingSupport[str](installer),
    ])
