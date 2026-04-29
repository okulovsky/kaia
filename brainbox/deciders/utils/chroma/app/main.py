from foundation_kaia.brainbox_utils import run_brainbox_app, InstallingSupport
from model import ChromaInstaller
from service import ChromaService

if __name__ == '__main__':
    installer = ChromaInstaller()
    service = ChromaService(chroma_path='/chroma', model_cache='/home/app/fastembed_cache')
    run_brainbox_app([service, InstallingSupport(installer)])
