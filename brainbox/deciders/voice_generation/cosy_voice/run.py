from brainbox.utils.compatibility import *
from brainbox.deciders.voice_generation.cosy_voice.controller import CosyVoiceController

if __name__ == '__main__':
    controller = CosyVoiceController()
    #resolve_dependencies(controller, exclude_pytorch=True)

    controller.install()
    controller.self_test()
    #controller.run_notebook()

    #test_on_arm64(controller)
