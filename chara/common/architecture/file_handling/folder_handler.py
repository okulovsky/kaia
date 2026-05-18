from pathlib import Path
from .types import ResultType

class FolderHandler:
    def __init__(self, folder: Path, result_types: tuple[ResultType]|None = None):
        self.folder = folder
        if result_types is None:
            result_types = ResultType.get_all_types()
        self.result_types = result_types

    def _find_file_and_type(self, name) -> tuple[Path,ResultType]|None:
        for type in self.result_types:
            path = self.folder/(name+type.get_extension())
            if path.is_file():
                return path, type
        return None


    def has_file(self, name) -> bool:
        return self._find_file_and_type(name) is not None

    def read(self, name):
        path, type = self._find_file_and_type(name)
        return type.read(path)

    def write(self, name, data):
        type = ResultType.find_type(self.result_types, data)
        type.write(data, self.folder/(name+type.get_extension()))

