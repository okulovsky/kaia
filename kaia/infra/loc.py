import subprocess
from typing import *
import pathlib
import shutil
import uuid
from pathlib import Path
import dotenv
import os
import sys
from uuid import uuid4

class _TempFile:
    def __init__(self, path: Path, dont_delete: bool):
        self.path = path
        self.dont_delete = dont_delete

    def __enter__(self):
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.dont_delete:
            if self.path.is_file():
                os.unlink(self.path)


class _TempFolder:
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




class _Loc:
    def __init__(self):
        self.root_folder = Path(__file__).parent.parent.parent

        env_file = self.root_folder/'environment.env'
        dotenv.load_dotenv(env_file)

        if isinstance(self.root_folder, pathlib.WindowsPath):
            self.is_windows = True
        else:
            self.is_windows = False
        self.temp_folder = self.root_folder/'temp'
        self.test_folder = self.temp_folder/'tests'
        self.externals_folder = self.root_folder/'externals'

        if 'CUSTOM_DATA_FOLDER' in os.environ:
            self.data_folder = Path(os.environ['CUSTOM_DATA_FOLDER'])
        else:
            self.data_folder = self.root_folder/'data'

        self.deciders_resources_folder = self.data_folder/'deciders_resources'
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(self.externals_folder, exist_ok=True)
        os.makedirs(self.data_folder, exist_ok=True)
        os.makedirs(self.test_folder, exist_ok=True)
        os.makedirs(self.deciders_resources_folder, exist_ok=True)

        self.conda_folder = Path(sys.executable).parent.parent.parent
        self.env_folder = Path(sys.executable).parent

        self.host_user_group_id = 1000
        self.username = ''
        self.hostname = ''
        if not self.is_windows:
            self.username = subprocess.check_output(['whoami']).decode('ascii')
            self.hostname = subprocess.check_output(['hostname']).decode('ascii')
            self.host_user_group_id = int(subprocess.check_output(['id', '-g']).decode('ascii'))

    def test_location(self, name):
        return self.test_folder/name/str(uuid.uuid4())

    def create_temp_file(self, subfolder: str, extension_without_leading_dot: str, dont_delete: bool = False) -> _TempFile:
        path = self.temp_folder/subfolder/f'{uuid4()}.{extension_without_leading_dot}'
        os.makedirs(path.parent, exist_ok=True)
        return _TempFile(path, dont_delete)

    def create_temp_folder(self, subfolder: str, dont_delete: bool = False) -> _TempFolder:
        return _TempFolder(self.temp_folder/subfolder, dont_delete)

    def wsl_translate(self, path: Union[str, Path]):
        if self.is_windows:
            import win32com.client as com
            parent_folder = str(path.parent)
            fso = com.Dispatch("Scripting.FileSystemObject")
            folder = fso.GetFolder(parent_folder)
            result = folder.path
            result = result.replace('\\','/')
            result = result+'/'+path.name
            result = '/mnt/'+result[0].lower()+'/'+result[3:]
            return result
        raise ValueError("Only makes sense under Windows")

Loc = _Loc()