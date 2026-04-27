import unittest
import tempfile
from pathlib import Path
from datetime import datetime

from foundation_kaia.marshalling.amenities.storage import Storage, FileDetails


class TestStorageList(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = Storage(Path(self.tmpdir))
        sub = Path(self.tmpdir) / 'data'
        sub.mkdir()
        (sub / 'img_001.png').write_bytes(b'png1')
        (sub / 'img_002.png').write_bytes(b'png2')
        (sub / 'doc.txt').write_bytes(b'text')

    def test_list_all_files(self):
        result = self.storage.list('data', None, None)
        self.assertCountEqual(['img_001.png', 'img_002.png', 'doc.txt'], result)

    def test_list_does_not_include_subdirectories_by_default(self):
        subdir = Path(self.tmpdir) / 'data' / 'sub'
        subdir.mkdir()
        (subdir / 'nested.png').write_bytes(b'nested')
        result = self.storage.list('data', None, None)
        self.assertCountEqual(['img_001.png', 'img_002.png', 'doc.txt'], result)

    def test_list_glob_includes_subdirectory_files(self):
        subdir = Path(self.tmpdir) / 'data' / 'sub'
        subdir.mkdir()
        (subdir / 'nested.png').write_bytes(b'nested')
        result = self.storage.list('data', None, None, glob=True)
        self.assertIn('sub/nested.png', result)
        self.assertIn('img_001.png', result)

    def test_list_glob_returns_relative_paths(self):
        subdir = Path(self.tmpdir) / 'data' / 'level1' / 'level2'
        subdir.mkdir(parents=True)
        (subdir / 'deep.txt').write_bytes(b'deep')
        result = self.storage.list('data', None, None, glob=True)
        self.assertIn('level1/level2/deep.txt', result)

    def test_list_with_prefix(self):
        result = self.storage.list('data', 'img_', None)
        self.assertCountEqual(['img_001.png', 'img_002.png'], result)

    def test_list_with_suffix(self):
        result = self.storage.list('data', None, '.png')
        self.assertCountEqual(['img_001.png', 'img_002.png'], result)

    def test_list_with_prefix_and_suffix(self):
        result = self.storage.list('data', 'img_', '.png')
        self.assertCountEqual(['img_001.png', 'img_002.png'], result)

    def test_list_no_match(self):
        result = self.storage.list('data', 'xyz_', None)
        self.assertEqual([], result)

    def test_list_with_path_object(self):
        result = self.storage.list(Path('data'), None, None)
        self.assertCountEqual(['img_001.png', 'img_002.png', 'doc.txt'], result)


class TestStorageListDetails(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = Storage(Path(self.tmpdir))
        sub = Path(self.tmpdir) / 'files'
        sub.mkdir()
        (sub / 'a.bin').write_bytes(b'aaa')
        (sub / 'b.bin').write_bytes(b'bbb')

    def test_list_details_returns_file_details(self):
        result = self.storage.list_details('files', None, None)
        self.assertEqual(2, len(result))
        for item in result:
            self.assertIsInstance(item, FileDetails)
            self.assertIn(item.name, ('a.bin', 'b.bin'))
            self.assertIsInstance(item.last_modification_date, datetime)

    def test_list_details_with_prefix(self):
        result = self.storage.list_details('files', 'a', None)
        self.assertEqual(1, len(result))
        self.assertEqual('a.bin', result[0].name)

    def test_list_details_modification_date_is_recent(self):
        before = datetime.now()
        result = self.storage.list_details('files', None, None)
        after = datetime.now()
        for item in result:
            self.assertGreaterEqual(item.last_modification_date, before.replace(microsecond=0))
            self.assertLessEqual(item.last_modification_date, after)

    def test_list_details_glob_includes_nested_files(self):
        subdir = Path(self.tmpdir) / 'files' / 'sub'
        subdir.mkdir()
        (subdir / 'c.bin').write_bytes(b'ccc')
        result = self.storage.list_details('files', None, None, glob=True)
        names = [item.name for item in result]
        self.assertIn('sub/c.bin', names)
        self.assertIn('a.bin', names)


class TestStorageOpen(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = Storage(Path(self.tmpdir))

    def _create_file(self, relpath, content):
        full = Path(self.tmpdir) / relpath
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(content)

    def test_open_returns_content(self):
        self._create_file('test.bin', b'hello world')
        result = b''.join(self.storage.open('test.bin'))
        self.assertEqual(b'hello world', result)

    def test_open_nested_path(self):
        self._create_file('sub/file.bin', b'nested content')
        result = b''.join(self.storage.open('sub/file.bin'))
        self.assertEqual(b'nested content', result)

    def test_open_path_object(self):
        self._create_file('data.bin', b'data')
        result = b''.join(self.storage.open(Path('data.bin')))
        self.assertEqual(b'data', result)

    def test_read_content_helper(self):
        self._create_file('test.bin', b'content here')
        result = self.storage.read('test.bin')
        self.assertEqual(b'content here', result)

    def test_open_empty_file(self):
        self._create_file('empty.bin', b'')
        result = b''.join(self.storage.open('empty.bin'))
        self.assertEqual(b'', result)

    def test_open_large_file(self):
        data = b'z' * 200_000
        self._create_file('big.bin', data)
        result = b''.join(self.storage.open('big.bin'))
        self.assertEqual(data, result)


class TestStorageUpload(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = Storage(Path(self.tmpdir))

    def test_upload_bytes(self):
        self.storage.upload('out.bin', b'uploaded data')
        result = (Path(self.tmpdir) / 'out.bin').read_bytes()
        self.assertEqual(b'uploaded data', result)

    def test_upload_path_object(self):
        self.storage.upload(Path('path_out.bin'), b'path upload')
        result = (Path(self.tmpdir) / 'path_out.bin').read_bytes()
        self.assertEqual(b'path upload', result)

    def test_upload_then_open(self):
        self.storage.upload('round_trip.bin', b'round trip data')
        result = b''.join(self.storage.open('round_trip.bin'))
        self.assertEqual(b'round trip data', result)

    def test_upload_overwrites_existing(self):
        self.storage.upload('overwrite.bin', b'old')
        self.storage.upload('overwrite.bin', b'new')
        result = b''.join(self.storage.open('overwrite.bin'))
        self.assertEqual(b'new', result)


class TestStorageIsFileIsDir(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.storage = Storage(Path(self.tmpdir))
        sub = Path(self.tmpdir) / 'data'
        sub.mkdir()
        (sub / 'file.bin').write_bytes(b'content')

    def test_is_file_existing_file(self):
        self.assertTrue(self.storage.is_file('data/file.bin'))

    def test_is_file_missing(self):
        self.assertFalse(self.storage.is_file('data/nope.bin'))

    def test_is_file_on_directory(self):
        self.assertFalse(self.storage.is_file('data'))

    def test_is_dir_existing_dir(self):
        self.assertTrue(self.storage.is_dir('data'))

    def test_is_dir_missing(self):
        self.assertFalse(self.storage.is_dir('no_such_dir'))

    def test_is_dir_on_file(self):
        self.assertFalse(self.storage.is_dir('data/file.bin'))


if __name__ == '__main__':
    unittest.main()
