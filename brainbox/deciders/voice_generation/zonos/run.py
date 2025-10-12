from brainbox.deciders import Zonos
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = Zonos.Controller()
    controller.install()
    controller.self_test()


