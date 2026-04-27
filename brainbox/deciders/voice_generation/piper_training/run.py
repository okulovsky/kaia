from brainbox.deciders import PiperTraining
from brainbox.utils.compatibility import *


if __name__ == '__main__':
    controller = PiperTraining.Controller()

    #resolve_dependencies(controller, exclude_pytorch=True, python_version='3.10.18')
    controller.install()
    controller.self_test()
