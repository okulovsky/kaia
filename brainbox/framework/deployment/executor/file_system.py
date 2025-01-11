from abc import ABC, abstractmethod
from pathlib import Path

class IFileSystem(ABC):
    @abstractmethod
    def upload_file(self, local_path: Path, remote_path: str):
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: Path):
        pass

    @abstractmethod
    def create_empty_folder(self, path: str|Path):
        pass

    @abstractmethod
    def is_file(self, remote_path: str):
        pass

    @abstractmethod
    def is_dir(self, remote_path: str):
        pass

    @abstractmethod
    def delete_file_or_folder(self, remote_path: str):
        pass
