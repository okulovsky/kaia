import traceback
from pathlib import Path
import shutil
from uuid import uuid4
import os
from dotenv import load_dotenv

class TempFile:
    def __init__(self, path: Path, dont_delete: bool):
        self.path = path
        self.dont_delete = dont_delete

    def __enter__(self):
        os.makedirs(self.path.parent, exist_ok=True)
        if self.path.is_file():
            os.unlink(self.path)
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.dont_delete:
            if self.path.is_file():
                try:
                    os.unlink(self.path)
                except:
                    print("Cannot delete test file:\n"+traceback.format_exc())


class TempFolder:
    def __init__(self, path: Path, dont_delete: bool = False):
        self.path = path
        self.dont_delete = dont_delete

    def __enter__(self):
        if self.path.is_dir():
            shutil.rmtree(self.path)
        os.makedirs(self.path)
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.dont_delete and self.path.is_dir():
            shutil.rmtree(self.path, ignore_errors=True)


class Locator:
    def __init__(self, root_path: Path|None = None):
        if root_path is None:
            root_path = Path(__file__).parent.parent.parent
        self._root_path = root_path
        load_dotenv(self._root_path/'environment.env')

    def _make_and_return(self, path) -> Path:
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def data_folder(self) -> Path:
        return self._make_and_return(self._root_path/'data')

    @property
    def resources_folder(self) -> Path:
        return self._make_and_return(self._root_path/'data/resources')

    @property
    def cache_folder(self) -> Path:
        return self._make_and_return(self._root_path/'temp/brainbox_cache')

    @property
    def temp_folder(self) -> Path:
        return self._make_and_return(self._root_path/'temp')

    @property
    def test_folder(self) -> Path:
        return self._make_and_return(self._root_path/'temp/tests')

    @property
    def self_test_path(self) -> Path:
        return self._make_and_return(self._root_path/'data/brainbox_self_test')

    @property
    def db_path(self) -> Path:
        return self.data_folder/'brainbox.db'

    @property
    def root_folder(self) -> Path:
        return self._root_path


    def create_test_file(self, extension_without_leading_dot: str|None = None, subfolder: str|None = None, dont_delete: bool = False) -> TempFile:
        path = self.test_folder
        if subfolder is not None:
            path /= subfolder
        name = str(uuid4())
        if extension_without_leading_dot is not None:
            name+= '.'+extension_without_leading_dot
        path/=name
        return TempFile(path, dont_delete)

    def create_test_folder(self, subfolder: str|None = None, dont_delete: bool = False) -> TempFolder:
        path = self.test_folder
        if subfolder is not None:
            path /= subfolder
        path /= str(uuid4())
        return TempFolder(path, dont_delete)

Loc = Locator()
