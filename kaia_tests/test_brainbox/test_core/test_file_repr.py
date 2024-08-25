from kaia.brainbox.core import File
from unittest import TestCase

class FileTestCase(TestCase):
    def test_file_to_str(self):
        file = [File('test',b'')]
        self.assertEqual('[File(test)]', str(file))