from brainbox.deciders import InsightFace

if __name__ == '__main__':
    controller = InsightFace.Controller()
    controller.install()
    controller.self_test()

