from brainbox.deciders.images.video_to_images.controller import VideoToImagesController
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = VideoToImagesController()
    #resolve_dependencies(controller)
    controller.install()
    controller.self_test()
    #test_on_arm64(controller)




