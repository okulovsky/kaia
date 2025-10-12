from brainbox.deciders import HelloBrainBox
from brainbox.utils.compatibility import resolve_dependencies, test_on_arm64

if __name__ == '__main__':
    controller = HelloBrainBox.Controller()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()
    #controller.run_notebook()

