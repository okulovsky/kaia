from brainbox.deciders import Nemotron
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = Nemotron.Controller()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()
