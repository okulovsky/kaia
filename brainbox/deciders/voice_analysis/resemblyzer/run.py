from brainbox.deciders import Resemblyzer
from unittest import TestCase

if __name__ == '__main__':
    controller = Resemblyzer.Controller()
    controller.install()
    controller.self_test()
    #controller.run_notebook()

