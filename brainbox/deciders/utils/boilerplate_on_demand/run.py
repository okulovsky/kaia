from brainbox.deciders import BoilerplateOnDemand
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = BoilerplateOnDemand.Controller()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()