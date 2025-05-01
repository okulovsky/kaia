import shutil
from unittest import TestCase
from brainbox import BrainBox
from nbconvert.preprocessors import ExecutePreprocessor
import nbformat
from pathlib import Path


def run_notebook(path):
    with BrainBox.Api.Test(port=8090) as api:
        tmp_folder = path.parent/'temp'
        if tmp_folder.is_dir():
            shutil.rmtree(tmp_folder)
        with open(path, encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
        ep.preprocess(nb, {'metadata': {'path': path.parent}})
        with open(path, 'w', encoding='utf-8') as f:
            nbformat.write(nb, path)

CHARA_ROOT = Path(__file__).parent.parent

class VoiceCloneUpsamplingDatasetTestCase(TestCase):
    def test_samples(self):
        run_notebook(CHARA_ROOT/'voice_clone/samples/samples.ipynb')

    def test_sentences(self):
        run_notebook(CHARA_ROOT/'voice_clone/sentences/sentences.ipynb')

    def test_voice_cloner(self):
        run_notebook(CHARA_ROOT/'voice_clone/voice_cloner/voice_cloner.ipynb')

    def test_upsampling(self):
        run_notebook(CHARA_ROOT/'voice_clone/upsampling/upsampling.ipynb')

    def test_training(self):
        run_notebook(CHARA_ROOT/'voice_clone/training/training.ipynb')

