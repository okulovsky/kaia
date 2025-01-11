from unittest import TestCase
from brainbox import File

class FileTestCase(TestCase):
    def test_file_str_repr(self):
        print(File('test', b'content', File.Kind.Text))