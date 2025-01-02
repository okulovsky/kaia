from brainbox.deciders import TortoiseTTS

if __name__ == '__main__':
    controller = TortoiseTTS.Controller()
    #controller.install()
    controller.self_test()