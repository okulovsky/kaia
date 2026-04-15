from foundation_kaia.brainbox_utils import run_brainbox_app
from service import ResemblyzerService


if __name__ == '__main__':
    service = ResemblyzerService()
    run_brainbox_app([service])
