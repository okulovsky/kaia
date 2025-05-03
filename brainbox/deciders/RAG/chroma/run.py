from brainbox.deciders.RAG.chroma.controller import ChromaController

if __name__ == '__main__':
    controller = ChromaController()
    controller.install()
    controller.self_test()