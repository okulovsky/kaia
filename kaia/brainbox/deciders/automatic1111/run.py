from kaia.brainbox.deciders.automatic1111.install import Automatic1111Installer, Automatic1111Settings
import requests

if __name__ == '__main__':
    installer = Automatic1111Installer(Automatic1111Settings())
    #installer.install()
    installer.run()
