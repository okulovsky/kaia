from foundation_kaia.brainbox_utils import run_brainbox_app, InstallingSupport, UniqueModelStorage
from model import WhisperKenLMInstaller
from service import WhisperKenLMService

if __name__ == '__main__':
    installer = WhisperKenLMInstaller()
    storage   = UniqueModelStorage(installer)
    service   = WhisperKenLMService(storage)
    run_brainbox_app([
        service,
        InstallingSupport(installer),
    ])
