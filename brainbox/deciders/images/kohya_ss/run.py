from brainbox.deciders import KohyaSS


if __name__ == '__main__':
    controller = KohyaSS.Controller()
    controller.install()
    controller.self_test()