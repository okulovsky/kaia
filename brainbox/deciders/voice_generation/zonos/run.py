from brainbox.deciders import Zonos
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = Zonos.Controller()
    #resolve_dependencies(controller, exclude_pytorch=True, python_version='3.11.11')
    controller.install()
    controller.self_test()


