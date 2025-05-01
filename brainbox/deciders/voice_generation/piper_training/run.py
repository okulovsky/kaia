from brainbox.deciders import PiperTraining

if __name__ == '__main__':
    controller = PiperTraining.Controller()
    controller.install()
    controller.self_test()
