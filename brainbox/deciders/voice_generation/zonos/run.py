from brainbox.deciders import Zonos

if __name__ == '__main__':
    controller = Zonos.Controller()
    controller.install()
    controller.self_test()