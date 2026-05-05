from unittest import TestCase
import pandas as pd
from foundation_kaia.misc import Loc
from chara.common.architecture.result_handling import (
    ResultType, FileResult, write_result, find_result, read_result
)


class ResultHandlingTestCase(TestCase):
    def _roundtrip(self, type: ResultType, data):
        with Loc.create_test_folder() as folder:
            write_result(folder, type, data)
            path = find_result(folder)
            self.assertIsNotNone(path)
            return read_result(path)

    def test_pickle(self):
        result = self._roundtrip(ResultType.Pickle, {"key": [1, 2, 3]})
        self.assertEqual({"key": [1, 2, 3]}, result)

    def test_json(self):
        result = self._roundtrip(ResultType.Json, {"a": 1})
        self.assertEqual({"a": 1}, result)

    def test_text(self):
        result = self._roundtrip(ResultType.Text, "hello world")
        self.assertEqual("hello world", result)

    def test_parquet(self):
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        result = self._roundtrip(ResultType.Parquet, df)
        pd.testing.assert_frame_equal(df, result)


    def test_find_result_none_when_missing(self):
        with Loc.create_test_folder() as folder:
            self.assertIsNone(find_result(folder))


