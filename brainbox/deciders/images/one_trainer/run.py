from brainbox.deciders import OneTrainer

if __name__ == '__main__':
    controller = OneTrainer.Controller()
    controller.install()
    controller.self_test()
