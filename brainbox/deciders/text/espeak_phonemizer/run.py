from brainbox.deciders.text.espeak_phonemizer.controller import EspeakPhonemizerController

if __name__ == '__main__':
    controller = EspeakPhonemizerController()
    controller.install()
    #controller.run_notebook()
    controller.self_test()