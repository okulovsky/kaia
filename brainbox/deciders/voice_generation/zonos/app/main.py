import os
os.environ['HF_HOME'] = '/resources/hf_cache'

from foundation_kaia.brainbox_utils import run_brainbox_app, InstallingSupport, UniqueModelStorage
from model import ZonosInstaller
from service import ZonosService


if __name__ == '__main__':
    installer = ZonosInstaller()
    storage = UniqueModelStorage(installer)
    service = ZonosService(storage)
    run_brainbox_app([
        service,
        InstallingSupport(installer),
    ])
