from kaia.brainbox.deciders.resemblyzer import ResemblyzerInstaller, ResemblyzerSettings
from unittest import TestCase

if __name__ == '__main__':
    installer = ResemblyzerInstaller(ResemblyzerSettings())
    installer.reinstall()
    installer.notebook_service.run()

