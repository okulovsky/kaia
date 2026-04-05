import os
os.environ['HF_HOME'] = '/resources'

from foundation_kaia.brainbox_utils import run_brainbox_app, SingleModelStorage, ModelLoadingSupport, ModelInstallingSupport
from model import WD14TaggerInstaller
from service import WD14TaggerService


if __name__ == '__main__':
    installer = WD14TaggerInstaller()
    storage = SingleModelStorage(installer, default_model='wd14-vit.v2')
    service = WD14TaggerService(storage)
    run_brainbox_app([
        service,
        ModelLoadingSupport(storage),
        ModelInstallingSupport[str](installer),
    ])
