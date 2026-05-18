import unittest

from .setup import *

# Larger than the old single-frame limit of 16 MB
_20_MB = 20 * 1024 * 1024


class TestHugeFile(unittest.TestCase):

    def test_huge_file_input(self):
        payload = b'x' * _20_MB
        with ExampleWsApi.test() as api:
            result = api.path_query_json_files(1, Data(7), payload, b'small', None)
        self.assertEqual(f"path_query_json_files:1,None,7,{_20_MB},5", result)


if __name__ == '__main__':
    unittest.main()
