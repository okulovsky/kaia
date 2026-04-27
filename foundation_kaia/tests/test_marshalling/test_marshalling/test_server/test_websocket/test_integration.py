import unittest
from collections.abc import Iterable

from .setup import *


class TestWsIntegration(unittest.TestCase):

    def test_integration(self):
        with ExampleWsApi.test() as api:
            # --- HTTP-parity: path / query / json / file / binary-stream input ---
            result = api.path_query(1, True)
            self.assertEqual("path_query:1,True", result)

            result = api.path_query_json(2, Data(5), False)
            self.assertEqual("path_query_json:2,False,5", result)

            result = api.path_query_json_files(3, Data(7), b'hello', b'world', True)
            self.assertEqual("path_query_json_files:3,True,7,5,5", result)

            result = api.path_query_file(4, b'test', True)
            self.assertEqual("path_query_file:4,True,4", result)

            result = api.path_query_stream(5, iter([b'abc', b'def']), False)
            self.assertEqual("path_query_stream:5,False,6", result)

            # --- WS-exclusive: CustomIterable output streaming ---
            result = list(api.stream_output(42))
            self.assertEqual(["item:42:0", "item:42:1", "item:42:2"], result)

            # --- WS-exclusive: JSON params combined with binary stream input ---
            result = api.json_and_stream(7, Data(99), iter([b'aaa', b'bb']))
            self.assertEqual("json_and_stream:7,99,5", result)

            # --- WS-exclusive: FileLike combined with binary stream input ---
            result = api.file_and_stream(9, b'hello', iter([b'aaa', b'bb']))
            self.assertEqual("file_and_stream:9,5,5", result)

            # --- WS-exclusive: roundtrip — streaming input and streaming output simultaneously ---
            result = b''.join(api.roundtrip(iter([b'aaa', b'bbb', b'ccc'])))
            self.assertEqual(b'aaabbbccc', result)

if __name__ == '__main__':
    unittest.main()
