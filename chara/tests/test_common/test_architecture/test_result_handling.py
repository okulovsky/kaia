from unittest import TestCase
import pandas as pd
from foundation_kaia.misc import Loc
from chara.common.architecture.result_handling import (
    write_result, find_result, read_result
)
from chara import CaseCollection, ICase
from dataclasses import dataclass
import json

@dataclass
class MyCase(ICase):
    x: int
    y: int



class ResultHandlingTestCase(TestCase):
    def _roundtrip(self, data):
        with Loc.create_test_folder() as folder:
            write_result(folder, data)
            path = find_result(folder)
            self.assertIsNotNone(path)
            content = path.read_bytes()
            return read_result(folder), content

    def test_pickle(self):
        result, _ = self._roundtrip({"key": [1, 2, 3]})
        self.assertEqual({"key": [1, 2, 3]}, result)

    def test_text(self):
        result, _ = self._roundtrip("hello world")
        self.assertEqual("hello world", result)

    def test_parquet(self):
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        result, _ = self._roundtrip(df)
        pd.testing.assert_frame_equal(df, result)

    def test_cases(self):
        c1 = MyCase(1, 2)
        c2 = MyCase(2, 3)
        c2.error = 'error'
        data = CaseCollection([c1, c2])
        result, content = self._roundtrip(data)
        json.loads(content)
        self.assertEqual(data.cases, result.cases)
        self.assertEqual(data.errors, result.errors)
        self.assertEqual(data.successes, result.successes)

    def test_json(self):
        data = {"s": "string", "i": 49, "dc": MyCase(1,2)}
        result, content = self._roundtrip(data)
        self.assertEqual(data, result)
        json.loads(content)


    def test_find_result_none_when_missing(self):
        with Loc.create_test_folder() as folder:
            self.assertIsNone(find_result(folder))




