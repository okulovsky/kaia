from brainbox.framework import BrainBoxServer, ControllerRegistry, BrainBoxServiceSettings



if __name__ == '__main__':
    settings = BrainBoxServiceSettings(ControllerRegistry.discover(), port=8090)
    server = BrainBoxServer(settings)
    server()