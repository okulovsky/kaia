from brainbox.framework import ControllerServer, ControllerRegistry, ControllerServerSettings
from brainbox.deciders import Boilerplate



if __name__ == '__main__':
    settings = ControllerServerSettings(ControllerRegistry.discover())
    server = ControllerServer(settings)
    server()