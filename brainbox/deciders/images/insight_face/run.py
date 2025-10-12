from brainbox.deciders import InsightFace
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = InsightFace.Controller()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()
    #test_on_arm64(controller)

