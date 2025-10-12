from brainbox.deciders.text.espeak_phonemizer.controller import EspeakPhonemizerController
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = EspeakPhonemizerController()
    #resolve_dependencies(controller)
    controller.install()
    #controller.run_notebook()
    controller.self_test()
    #test_on_arm64(controller)