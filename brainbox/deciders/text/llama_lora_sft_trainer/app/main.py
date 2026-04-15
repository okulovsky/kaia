from foundation_kaia.brainbox_utils import run_brainbox_app
from service import LlamaLoraSFTTrainerService

if __name__ == '__main__':
    run_brainbox_app([LlamaLoraSFTTrainerService()], True)
