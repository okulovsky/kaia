from brainbox.deciders.images.yolo.controller import YoloController


if __name__ == '__main__':
    controller = YoloController()
    controller.install()
    controller.self_test()
