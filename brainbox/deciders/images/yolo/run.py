from brainbox.deciders.images.yolo.controller import YoloController
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = YoloController()

    resolve_dependencies(controller)
    test_on_arm64(controller)

    controller.install()
    controller.self_test()
