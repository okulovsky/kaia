from brainbox.deciders import BoilerplateServer

if __name__ == '__main__':
    controller = BoilerplateServer.Controller()
    controller.install()
    controller.self_test()