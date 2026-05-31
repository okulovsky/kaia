from brainbox.deciders.images.comfyui.controller import ComfyUIController
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = ComfyUIController()

    #resolve_dependencies(controller)

    controller.install()
    controller.self_test()
