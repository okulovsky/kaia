from brainbox.framework import BrainBoxServer, ControllerRegistry, BrainBoxServerSettings, BrainBoxLocations
from foundation_kaia.misc import Loc

if __name__ == '__main__':
    settings = BrainBoxServerSettings(ControllerRegistry.discover(), BrainBoxLocations.default(), port=8090)
    server = BrainBoxServer(settings)
    server()
