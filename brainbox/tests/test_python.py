from unittest import TestCase
import sys

class PythonTestCase(TestCase):
    def test_python(self):
        print(f'PYTHON_VERSION {sys.version}', file=sys.stderr)
