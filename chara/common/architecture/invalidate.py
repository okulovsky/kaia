from pathlib import Path
import shutil
from .result_handling import remove_result

def invalidate(path: Path, root: Path, down: bool):
    if not path.is_absolute():
        path = root / path

    if not path.is_relative_to(root):
        raise ValueError(f"Path {path} must be relative to root {root}")

    if not path.is_dir():
        raise ValueError(f"Path {path} is not a directory")

    if down:
        shutil.rmtree(path)
    else:
        remove_result(path)

    if path == root:
        return

    while path != root:
        parent = path.parent

        path_index = int(path.name.split('-')[0])
        for s in list(parent.iterdir()):
            if not s.is_dir():
                continue
            try:
                index = int(s.name.split('-')[0])
            except Exception:
                continue
            if index > path_index:
                shutil.rmtree(s)

        remove_result(parent)

        path = parent
