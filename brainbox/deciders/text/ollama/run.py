from brainbox.deciders import Ollama



if __name__ == '__main__':
    controller = Ollama.Controller()
    controller.install()
    controller.self_test()







