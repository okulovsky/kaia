from foundation_kaia.brainbox_utils import run_brainbox_app
from service import OneTrainerService

if __name__ == '__main__':
    run_brainbox_app([OneTrainerService()], True)
