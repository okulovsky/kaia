import json
import unittest

import requests

from foundation_kaia.marshalling import TestApi
from .test_integration import ExampleServer

BASE = 'http://127.0.0.1:8888'


class TestRawRequests(unittest.TestCase):
    def test_path_query(self):
        with TestApi(lambda _: None, ExampleServer(8888)):
            resp = requests.post(f'{BASE}/example-impl/path-query/1?flag=True')
            self.assertEqual(200, resp.status_code)
            self.assertEqual('path_query:1,True', resp.json())

    def test_path_query_json(self):
        with TestApi(lambda _: None, ExampleServer(8888)):
            resp = requests.post(
                f'{BASE}/example-impl/path-query-json/2?flag=False',
                data=json.dumps({'data': {'value': 5}}),
            )
            self.assertEqual(200, resp.status_code)
            self.assertEqual('path_query_json:2,False,5', resp.json())

    def test_path_query_file(self):
        with TestApi(lambda _: None, ExampleServer(8888)):
            resp = requests.post(
                f'{BASE}/example-impl/path-query-file/4?flag=True',
                data=b'test',
            )
            self.assertEqual(200, resp.status_code)
            self.assertEqual('path_query_file:4,True,4', resp.json())

    def test_path_query_stream(self):
        with TestApi(lambda _: None, ExampleServer(8888)):
            resp = requests.post(
                f'{BASE}/example-impl/path-query-stream/5?flag=False',
                data=b'abcdef',
            )
            self.assertEqual(200, resp.status_code)
            self.assertEqual('path_query_stream:5,False,6', resp.json())

    def test_path_query_json_files(self):
        with TestApi(lambda _: None, ExampleServer(8888)):
            resp = requests.post(
                f'{BASE}/example-impl/path-query-json-files/3?flag=True',
                files=[
                    ('json_arguments', json.dumps({'data': {'value': 7}})),
                    ('f1', b'hello'),
                    ('f2', b'world'),
                ],
            )
            self.assertEqual(200, resp.status_code)
            self.assertEqual('path_query_json_files:3,True,7,5,5', resp.json())



if __name__ == '__main__':
    unittest.main()
