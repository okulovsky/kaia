from brainbox.deciders import Chroma

if __name__ == '__main__':
    controller = Chroma.Controller()
    controller.install()
    controller.self_test()
