import sys, json
from pathlib import Path
from brainbox.deciders import WhisperKenLM

if __name__ == '__main__':
    controller = WhisperKenLM.Controller()
    controller.install()
    controller.self_test()