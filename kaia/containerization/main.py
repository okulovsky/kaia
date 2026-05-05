import time
from kaia.app import KaiaAppSettings
from foundation_kaia.misc import Loc
from kaia.containerization.starter import start_kaia

if __name__ == '__main__':
    settings = KaiaAppSettings()
    settings.custom_avatar_resources_folder = Loc.root_folder / 'kaia/app/files/avatar-resources'
    start_kaia(settings)
    while True:
        time.sleep(1)

