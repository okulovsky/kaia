from foundation_kaia.brainbox_utils import run_brainbox_app
from service import EspeakPhonemizerService


if __name__ == '__main__':
    service = EspeakPhonemizerService()
    run_brainbox_app([service])
