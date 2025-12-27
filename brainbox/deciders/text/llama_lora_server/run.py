from brainbox.deciders import LlamaLoraServer
from brainbox.utils.compatibility import *

if __name__ == "__main__":
    controller = LlamaLoraServer.Controller()
    controller.install()
    controller.self_test()
