from brainbox.deciders import BoilerplateServer
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = BoilerplateServer.Controller()
    #resolve_dependencies(controller)

    controller.install()
    controller.self_test()

    #test_on_arm64(controller)
