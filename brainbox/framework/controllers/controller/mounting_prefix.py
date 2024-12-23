from pathlib import Path
class MountingPrefix:
    def __init__(self, prefix: str|Path = ''):
        self.prefix = str(prefix)

    def remove_from(self, path: Path|str) -> Path:
        path = str(path)
        if not path.startswith(self.prefix):
            raise ValueError(f"Cannot remove mounting prefix {self.prefix} from path {path}")
        return Path(path[len(self.prefix):])