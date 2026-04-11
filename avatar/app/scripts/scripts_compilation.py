import hashlib
import subprocess
from pathlib import Path

HASH_FILE = '.src_hash'


def _compute_folder_hash(folder: Path) -> str:
    hasher = hashlib.md5()
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            hasher.update(path.relative_to(folder).as_posix().encode())
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def compile(src_folder: Path, dst_folder: Path):
    """
    1. Compute the hash of src folder, including the subfolders
    2. Check if dst folder exists. If it does, check hash file there. If it exists and contains the same hash as computed in (1), skip (3)
    3. Compile the scripts as it's done in ../typescript.py, outputting directly to dst_folder
    """
    src_hash = _compute_folder_hash(src_folder)

    hash_file = dst_folder / HASH_FILE
    if dst_folder.exists() and hash_file.exists():
        if hash_file.read_text().strip() == src_hash:
            return

    web_root = src_folder.parent

    node_modules = web_root / 'node_modules'
    if not node_modules.exists():
        npm_install = subprocess.run(
            ['npm', 'install'],
            cwd=str(web_root),
            capture_output=True,
            text=True,
        )
        if npm_install.returncode != 0:
            raise RuntimeError(f"npm install failed:\n{npm_install.stdout}\n{npm_install.stderr}")

    vite_js = web_root / 'node_modules' / 'vite' / 'bin' / 'vite.js'
    if not vite_js.exists():
        raise RuntimeError(f"Vite not found at {vite_js} even after npm install")

    node = subprocess.check_output(['bash', '-ic', 'which node'], text=True).strip()
    result = subprocess.run(
        [node, str(vite_js), 'build', '--outDir', str(dst_folder)],
        cwd=str(web_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"vite build failed:\n{result.stdout}\n{result.stderr}")

    hash_file.write_text(src_hash)


