from brainbox.deciders import Piper

if __name__ == "__main__":
    controller = Piper.Controller()
    controller.install()
    controller.self_test()

