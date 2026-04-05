from brainbox.framework import BrainBoxServer, ControllerRegistry, BrainBoxServerSettings



if __name__ == '__main__':
    settings = BrainBoxServerSettings(ControllerRegistry.discover(), port=8090)
    server = BrainBoxServer(settings)
    server()