from brainbox.deciders.images.yolo.controller import YoloController
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = YoloController()

    #resolve_dependencies(controller)

    controller.install()
    controller.self_test()

    #test_on_arm64(controller)

