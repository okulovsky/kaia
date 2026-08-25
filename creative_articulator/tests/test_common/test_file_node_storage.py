import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from creative_articulator.common import FileNodeStorage


@dataclass
class Foo:
    value: str = 'foo'


@dataclass
class Bar:
    value: str = 'bar'


class TestFileNodeStorageDelete(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.folder = Path(self._tmp.name)
        self.storage = FileNodeStorage(self.folder)

    def test_delete_removes_file_and_in_memory_value(self):
        self.storage.set(Foo, Foo())
        self.assertTrue((self.folder / 'Foo.json').exists())

        self.storage.delete(Foo)

        self.assertFalse((self.folder / 'Foo.json').exists())
        self.assertFalse(self.storage.has(Foo))

    def test_delete_of_key_never_set_does_not_raise(self):
        self.storage.delete(Foo)

    def test_delete_does_not_affect_other_keys(self):
        self.storage.set(Foo, Foo())
        self.storage.set(Bar, Bar())

        self.storage.delete(Foo)

        self.assertFalse(self.storage.has(Foo))
        self.assertTrue(self.storage.has(Bar))

    def test_delete_of_memory_only_key_clears_it_without_touching_disk(self):
        self.storage.memory_only(Foo)
        self.storage.set(Foo, Foo())

        self.storage.delete(Foo)

        self.assertFalse(self.storage.has(Foo))


if __name__ == '__main__':
    unittest.main()
