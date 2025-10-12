from brainbox.deciders import OpenVoice
from brainbox.utils.compatibility import *

if __name__ == "__main__":
    controller = OpenVoice.Controller()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()

    # test_on_arm64(controller)
