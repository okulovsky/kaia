import os
os.environ['HF_HOME'] = '/resources/hf_cache'

from foundation_kaia.brainbox_utils import (
    run_brainbox_app, ModelLoadingSupport, ModelInstallingSupport,
    InstallingSupport, SingleModelStorage
)
from model import ParlerTtsInstaller
from service import ParlerTtsService


if __name__ == '__main__':
    installer = ParlerTtsInstaller()
    storage = SingleModelStorage(installer, default_model='mini-v1')
    service = ParlerTtsService(storage)
    run_brainbox_app([
        service,
        ModelLoadingSupport(storage),
        ModelInstallingSupport[str](installer),
        InstallingSupport(installer),
    ])
