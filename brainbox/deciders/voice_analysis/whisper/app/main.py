from foundation_kaia.brainbox_utils import (
    run_brainbox_app, ModelLoadingSupport, ModelInstallingSupport,
    InstallingSupport, SingleModelStorage
)
from model import WhisperInstaller
from service import WhisperService

if __name__ == '__main__':
    installer = WhisperInstaller()
    storage = SingleModelStorage(installer, default_model='base')
    service = WhisperService(storage)
    run_brainbox_app([
        service,
        ModelLoadingSupport(storage),
        ModelInstallingSupport[str](installer),
    ])
