import hashlib
import shutil
from pathlib import Path

HASH_FILE = '.src_hash'


def _compute_folder_hash(folder: Path) -> str:
    hasher = hashlib.md5()
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            hasher.update(path.relative_to(folder).as_posix().encode())
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def copy_files(src_folder: Path, dst_folder: Path):
    src_hash = _compute_folder_hash(src_folder)

    hash_file = dst_folder / HASH_FILE
    if dst_folder.exists() and hash_file.exists():
        if hash_file.read_text().strip() == src_hash:
            return

    dst_folder.mkdir(parents=True, exist_ok=True)
    for path in src_folder.iterdir():
        if path.is_file():
            shutil.copy2(path, dst_folder / path.name)

    hash_file.write_text(src_hash)
