from brainbox.deciders import LlamaLoraSFTTrainer
from brainbox.utils.compatibility import *

if __name__ == '__main__':
    controller = LlamaLoraSFTTrainer.Controller()
    controller.install()
    controller.self_test()