from brainbox.deciders.voice_analysis.whisper import Whisper
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = Whisper.Controller()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()

    #test_on_arm64(controller)

