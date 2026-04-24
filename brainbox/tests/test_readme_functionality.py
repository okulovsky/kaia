from brainbox import BrainBox
from unittest import TestCase
from foundation_kaia.releasing.mddoc import run_doc_files
from pathlib import Path


class ReadmeTestCase(TestCase):
    def test_readme(self):
        with BrainBox.Api.test(port=8090) as api:
            run_doc_files(self, Path(__file__).parent.parent/'doc')


