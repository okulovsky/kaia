from brainbox.deciders import TortoiseTTS
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = TortoiseTTS.Controller()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()