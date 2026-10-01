from brainbox.deciders import ParlerTts
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = ParlerTts.Controller()
    #resolve_dependencies(controller, exclude_pytorch=True)

    controller.install()
    controller.self_test()
