import unittest
from pathlib import Path
from foundation_kaia.releasing.mddoc import run_doc_files

DOC_ROOT = Path(__file__).parent.parent / 'doc'


class DocFilesTestCase(unittest.TestCase):
    def test_doc_files(self):
        run_doc_files(self, DOC_ROOT)
