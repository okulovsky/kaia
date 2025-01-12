from brainbox.deciders import WD14Tagger

if __name__ == '__main__':
    controller = WD14Tagger.Controller()
    controller.install()
    controller.self_test()

