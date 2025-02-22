from brainbox.deciders import Vosk

if __name__ == '__main__':
    controller = Vosk.Controller()
    controller.install()
    controller.self_test()