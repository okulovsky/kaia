from brainbox.deciders import WhisperX

if __name__ == '__main__':
    controller = WhisperX.Controller()
    controller.install()
    controller.self_test()