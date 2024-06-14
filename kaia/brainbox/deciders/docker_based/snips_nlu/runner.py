import yaml

from kaia.brainbox.deciders.docker_based.snips_nlu.installer import SnipsNLUSettings, SnipsNLUInstaller
from unittest import TestCase

if __name__ == '__main__':
    settings = SnipsNLUSettings()
    installer = SnipsNLUInstaller(settings)
    installer.install()
    installer.get_service_endpoint().run()
    installer.self_test(TestCase())

    #installer.notebook_endpoint.run()

