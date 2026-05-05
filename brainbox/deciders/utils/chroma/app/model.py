from foundation_kaia.brainbox_utils import Installer

MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'


class ChromaInstaller(Installer[str]):
    def _execute_installation(self):
        from fastembed import TextEmbedding
        TextEmbedding(MODEL_NAME, cache_dir='/home/app/fastembed_cache')
