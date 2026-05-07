import hashlib
import subprocess
import shutil
import sys
from pathlib import Path
from typing import Optional

HASH_FILE = '.src_hash'


def _compute_folder_hash(folder: Path) -> str:
    hasher = hashlib.md5()
    for path in sorted(folder.rglob('*')):
        if path.is_file():
            hasher.update(path.relative_to(folder).as_posix().encode())
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def _resolve_executable(*candidates: str) -> Optional[str]:
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _find_node() -> str:
    if sys.platform == 'win32':
        node = _resolve_executable('node.exe', 'node')
    else:
        node = _resolve_executable('node')
        if not node:
            nvm_dir = Path.home() / '.nvm' / 'versions' / 'node'
            if nvm_dir.exists():
                versions = sorted(nvm_dir.iterdir(), reverse=True)
                for version in versions:
                    candidate = version / 'bin' / 'node'
                    if candidate.exists():
                        return str(candidate)

    if node:
        return node

    raise RuntimeError("Node.js executable was not found in PATH")


def _find_npm(node_path: Optional[str] = None) -> str:
    npm = _resolve_executable('npm.cmd', 'npm.exe', 'npm') if sys.platform == 'win32' else _resolve_executable('npm')
    if npm:
        return npm

    # Fallback: npm may sit next to node but still be absent from PATH.
    resolved_node = node_path or _find_node()
    node_dir = Path(resolved_node).parent
    for candidate in ('npm.cmd', 'npm.exe', 'npm'):
        candidate_path = node_dir / candidate
        if candidate_path.exists():
            return str(candidate_path)

    raise RuntimeError(
        f"NPM executable was not found in PATH or near node at '{resolved_node}'"
    )


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

    node = _find_node()
    npm_install = subprocess.run(
        [_find_npm(node), 'install', '--include=optional'],
        cwd=str(web_root),
        capture_output=True,
        text=True,
    )
    if npm_install.returncode != 0:
        raise RuntimeError(f"npm install failed:\n{npm_install.stdout}\n{npm_install.stderr}")

    vite_js = web_root / 'node_modules' / 'vite' / 'bin' / 'vite.js'
    if not vite_js.exists():
        raise RuntimeError(f"Vite not found at {vite_js} even after npm install")

    result = subprocess.run(
        [node, str(vite_js), 'build', '--outDir', str(dst_folder)],
        cwd=str(web_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"vite build failed:\n{result.stdout}\n{result.stderr}")

    hash_file.write_text(src_hash)
