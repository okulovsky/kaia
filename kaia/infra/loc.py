import pathlib
import uuid
from pathlib import Path
import dotenv
import os
import sys
from uuid import uuid4

class _TempFile:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path.is_file():
            os.unlink(self.path)


class _Loc:
    def __init__(self):
        self.root_folder = Path(__file__).parent.parent.parent
        if isinstance(self.root_folder, pathlib.WindowsPath):
            self.is_windows = True
        else:
            self.is_windows = False
        self.temp_folder = self.root_folder/'temp'
        self.test_folder = self.temp_folder/'tests'
        self.externals_folder = self.root_folder/'externals'
        self.data_folder = self.root_folder/'data'
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(self.externals_folder, exist_ok=True)
        os.makedirs(self.data_folder, exist_ok=True)
        os.makedirs(self.test_folder, exist_ok=True)
        env_file = self.root_folder/'environment.env'
        dotenv.load_dotenv(env_file)

        self.conda_folder = Path(sys.executable).parent.parent.parent
        self.env_folder = Path(sys.executable).parent

        if self.is_windows:
            self.call_conda = f"call {self.conda_folder/'condabin/conda.bat'}"
        else:
            self.call_conda = self.conda_folder.parent/'bin/conda'

    def get_python_by_env(self, env):
        if self.is_windows:
            return self.conda_folder / 'envs' / env / 'python.exe'
        else:
            return self.conda_folder/env/'bin/python'

    def get_ffmpeg(self):
        if self.is_windows:
            return self.root_folder.parent/'ffmpeg/bin/ffmpeg'
        else:
            return 'ffmpeg'

    def test_location(self, name):
        return self.test_folder/name/str(uuid.uuid4())

    def temp_file(self, subfolder: str, extension: str) -> _TempFile:
        path = self.temp_folder/subfolder/f'{uuid4()}.{extension}'
        os.makedirs(path.parent, exist_ok=True)
        return _TempFile(path)

Loc = _Loc()