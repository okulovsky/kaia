from brainbox.deciders import Vosk
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = Vosk.Controller()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()
    #test_on_arm64(controller)