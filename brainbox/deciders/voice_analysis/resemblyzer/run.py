from brainbox.deciders import Resemblyzer
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = Resemblyzer.Controller()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()
    #controller.run_notebook()
    # test_on_arm64(controller)


