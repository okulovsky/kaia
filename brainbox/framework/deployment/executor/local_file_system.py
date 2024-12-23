import os
from pathlib import Path
import shutil
from .file_system import IFileSystem


class LocalFileSystem(IFileSystem):
    def upload_file(self, local_path: Path, remote_path: str):
        os.makedirs(Path(remote_path).parent, exist_ok=True)
        shutil.copy(local_path, remote_path)

    def download_file(self, remote_path: str, local_path: Path):
        shutil.copy(remote_path, local_path)

    def create_empty_folder(self, path: str|Path):
        os.makedirs(path, exist_ok=True)

    def is_file(self, remote_path: str):
        return Path(remote_path).is_file()

    def is_dir(self, remote_path: str):
        return Path(remote_path).is_dir()

    def delete_file_or_folder(self, remote_path: str):
        if self.is_file(remote_path):
            os.unlink(remote_path)
        elif self.is_dir(remote_path):
            shutil.rmtree(remote_path)
