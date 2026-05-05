import runpy
from pathlib import Path
from unittest import TestCase


def run_doc_files(test_case: TestCase, doc_folder: Path) -> None:
    for file in sorted(doc_folder.glob('doc_*.py'), key=lambda f: f.name):
        print(f"Running documentation test in {file}")
        with test_case.subTest(file=file.name):
            runpy.run_path(str(file), run_name='__main__')
