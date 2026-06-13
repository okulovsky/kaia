import dataclasses
from pathlib import Path
from unittest import TestCase

import pandas as pd
from foundation_kaia.misc import Loc

from chara.common.architecture.file_handling.folder_handler import FolderHandler
from chara.common.architecture.file_handling.types.simple_types import (
    TextType, PathType, ParquetType, JsonType, PickleType,
)


@dataclasses.dataclass
class Point:
    x: float
    y: float


@dataclasses.dataclass
class Named:
    name: str
    point: Point


class JsonTypeAcceptsDataTestCase(TestCase):
    def setUp(self):
        self.t = JsonType()

    def test_accepts_dataclass(self):
        self.assertTrue(self.t.accepts_data(Point(1.0, 2.0)))

    def test_accepts_nested_dataclass(self):
        self.assertTrue(self.t.accepts_data(Named("a", Point(0.0, 0.0))))

    def test_accepts_list_of_dataclasses(self):
        self.assertTrue(self.t.accepts_data([Point(1.0, 2.0), Point(3.0, 4.0)]))

    def test_accepts_empty_list(self):
        self.assertTrue(self.t.accepts_data([]))

    def test_accepts_dict_of_dataclasses(self):
        self.assertTrue(self.t.accepts_data({"p": Point(1.0, 2.0)}))

    def test_accepts_empty_dict(self):
        self.assertTrue(self.t.accepts_data({}))

    def test_accepts_plain_string(self):
        self.assertTrue(self.t.accepts_data("hello"))

    def test_accepts_int(self):
        self.assertTrue(self.t.accepts_data(42))

    def test_accepts_list_with_mixed_primitives_and_dataclasses(self):
        self.assertTrue(self.t.accepts_data([Point(1.0, 2.0), "oops"]))

    def test_rejects_dict_with_non_str_key(self):
        self.assertFalse(self.t.accepts_data({1: Point(1.0, 2.0)}))

    def test_accepts_dict_with_primitive_value(self):
        self.assertTrue(self.t.accepts_data({"x": 42}))


class FolderHandlerRoundtripTestCase(TestCase):
    def _roundtrip(self, data):
        with Loc.create_test_folder() as folder:
            h = FolderHandler(folder)
            h.write("result", data)
            self.assertTrue(h.has_file("result"))
            return h.read("result")

    def test_text_roundtrip(self):
        result = self._roundtrip("hello world")
        self.assertEqual("hello world", result)

    def test_path_roundtrip(self):
        p = Path("/tmp/some/path")
        result = self._roundtrip(p)
        self.assertEqual(p, result)

    def test_parquet_roundtrip(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = self._roundtrip(df)
        pd.testing.assert_frame_equal(df, result)

    def test_json_roundtrip(self):
        data = Point(1.5, 2.5)
        result = self._roundtrip(data)
        self.assertEqual(data, result)

    def test_json_list_roundtrip(self):
        data = [Point(1.0, 2.0), Point(3.0, 4.0)]
        result = self._roundtrip(data)
        self.assertEqual(data, result)

    def test_pickle_roundtrip(self):
        data = {"arbitrary": [1, 2, 3]}
        result = self._roundtrip(data)
        self.assertEqual(data, result)

    def test_has_file_false_when_missing(self):
        with Loc.create_test_folder() as folder:
            h = FolderHandler(folder)
            self.assertFalse(h.has_file("missing"))

    def test_type_priority_text_over_pickle(self):
        with Loc.create_test_folder() as folder:
            h = FolderHandler(folder)
            h.write("result", "some text")
            self.assertTrue((folder / "result.txt").is_file())
            self.assertFalse((folder / "result.pickle").is_file())

    def test_type_priority_json_over_pickle(self):
        with Loc.create_test_folder() as folder:
            h = FolderHandler(folder)
            h.write("result", Point(0.0, 0.0))
            self.assertTrue((folder / "result.json").is_file())
            self.assertFalse((folder / "result.pickle").is_file())
