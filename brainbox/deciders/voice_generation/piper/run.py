from brainbox.deciders import Piper
from brainbox.utils.compatibility import *

if __name__ == "__main__":
    controller = Piper.Controller()
    #resolve_dependencies(controller,'3.11')
    #controller.install()
    #controller.self_test()
    test_on_arm64(controller)
