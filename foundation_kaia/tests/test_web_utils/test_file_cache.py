import os
import unittest
from foundation_kaia.web_utils.file_cache import FileCacheComponent, FileCacheApi, ApiError
from foundation_kaia.fork import Fork
from pathlib import Path
from flask import Flask
from foundation_kaia.marshalling import ApiUtils

BASEDIR = Path(__file__).parent/'temp'

def run_flask():
    app = Flask('test_server')
    FileCacheComponent(BASEDIR).register(app)
    app.run('127.0.0.1', 8000)


class FileApiBlueprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = BASEDIR
        cls.fork = Fork(run_flask)
        cls.fork.__enter__()
        cls.api = FileCacheApi('http://127.0.0.1:8000')
        ApiUtils.wait_for_reply(cls.api.base, 10)

        (cls.base_dir / "a").mkdir(parents=True, exist_ok=True)
        (cls.base_dir / "a" / "sub").mkdir(parents=True, exist_ok=True)
        (cls.base_dir / "a" / "x.txt").write_text("hello", encoding="utf-8")
        (cls.base_dir / "a" / "img_1.png").write_bytes(b"\x89PNG\x0d\x0a\x1a\x0a")
        (cls.base_dir / "a" / "img_2.png").write_bytes(b"\x89PNG\x0d\x0a\x1a\x0a\x00")
        (cls.base_dir / "a" / "sub" / "y.bin").write_bytes(b"\x00\x01\x02")


    @classmethod
    def tearDownClass(cls):
        cls.fork.__exit__(None, None, None)


    def test_upload_and_open(self):
        data = b"abcdefg"
        self.api.upload(data, "new/new.bin")
        on_disk = (self.base_dir / "new" / "new.bin").read_bytes()
        self.assertEqual(data, on_disk)
        got = self.api.open("new/new.bin")
        self.assertEqual(data, got)

    def test_upload_without_name(self):
        data = b'abc'
        result = self.api.upload(data)
        on_disk = (self.base_dir/result).read_bytes()
        self.assertEqual(data, on_disk)
        self.assertEqual(data, self.api.open(result))


    def test_download_to_path(self):
        dest = Path(self.base_dir) / "dl" / "x_copy.txt"
        out = self.api.download("a/x.txt", dest)
        self.assertTrue(out.exists())
        self.assertEqual(out.read_text(encoding="utf-8"), "hello")

    def test_head_file(self):
        h = self.api.head("a/x.txt")
        self.assertEqual(h["status"], 200)
        self.assertEqual(h["content_length"], 5)

    def test_delete_file(self):
        self.api.upload(b"bye", "a/will_delete.bin")
        self.assertTrue((self.base_dir / "a" / "will_delete.bin").exists())
        res = self.api.delete("a/will_delete.bin")
        self.assertEqual(res["status"], "ok")
        self.assertFalse((self.base_dir / "a" / "will_delete.bin").exists())
        with self.assertRaises(ApiError) as ctx:
            self.api.delete("a/will_delete.bin")
        self.assertIn("404", str(ctx.exception))


    def test_list_nonrecursive_and_filters(self):
        lst = self.api.list("a", recursive=False)
        self.assertCountEqual(lst, ["x.txt", "img_1.png", "img_2.png"])

        lst_pref = self.api.list("a", prefix="img_", recursive=False)
        self.assertCountEqual(lst_pref, ["img_1.png", "img_2.png"])

        lst_suf = self.api.list("a", suffix=".txt", recursive=False)
        self.assertEqual(lst_suf, ["x.txt"])

        lst_none = self.api.list("a", prefix="img_", suffix=".txt", recursive=False)
        self.assertEqual(lst_none, [])

    def test_list_recursive(self):
        lst = self.api.list("a", recursive=True)
        self.assertIn("x.txt", lst)
        self.assertIn("img_1.png", lst)
        self.assertIn("img_2.png", lst)
        self.assertIn(str(Path("sub") / "y.bin"), lst)

    def test_head_dir_exists_and_404(self):
        ok = self.api.exists("a")
        self.assertTrue(ok)
        with self.assertRaises(ApiError) as ctx:
            self.api.exists("no_such_dir")
        self.assertIn("404", str(ctx.exception))



