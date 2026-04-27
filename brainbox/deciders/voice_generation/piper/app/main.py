from foundation_kaia.brainbox_utils import run_brainbox_app, ModelInstallingSupport
from model import PiperModelSpec, PiperInstaller
from service import PiperService


if __name__ == '__main__':
    installer = PiperInstaller()
    service = PiperService()
    run_brainbox_app([
        service,
        ModelInstallingSupport[PiperModelSpec](installer),
    ])
