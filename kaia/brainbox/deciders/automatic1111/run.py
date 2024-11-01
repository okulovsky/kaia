from kaia.brainbox.deciders.automatic1111.install import Automatic1111Installer, Automatic1111Settings, Automatic1111
import requests
from pathlib import Path
import webbrowser
import base64
from kaia.infra import FileIO


if __name__ == '__main__':
    installer = Automatic1111Installer(Automatic1111Settings())
    #installer.brainbox_self_test()
    #installer.reinstall()
    api:Automatic1111 = installer.run_in_any_case_and_create_api()
    #webbrowser.open(f'http://{api.address}:{api.settings.port}')
    #api.interrogate()
    #upscale()
    #api.upscale(FileIO.read_bytes(Path(__file__).parent/'image.png'))


