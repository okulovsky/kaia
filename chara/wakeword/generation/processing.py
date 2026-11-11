"""Bounded file exchange between Chara and remote BrainBox workers."""

import json
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath


def extract_archive(source: Path, destination: Path, max_bytes: int = 100 * 1024**3):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        members = archive.infolist()
        if sum(m.file_size for m in members) > max_bytes:
            raise ValueError("archive exceeds uncompressed size limit")
        seen = set()
        for member in members:
            name = member.filename
            relative = PurePosixPath(name)
            mode = member.external_attr >> 16
            if (
                not name
                or relative.is_absolute()
                or ".." in relative.parts
                or "\\" in name
                or ":" in name
                or stat.S_ISLNK(mode)
            ):
                raise ValueError(f"unsafe archive member: {name}")
            target = (destination / name).resolve()
            if (
                not target.is_relative_to(destination)
                or target in seen
                or target.exists()
            ):
                raise ValueError(f"duplicate or existing archive member: {name}")
            seen.add(target)
        for member in members:
            target = destination / member.filename
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
    return destination


def create_archive(path: Path, files: dict[str, Path], manifest: dict):
    temporary = Path(path).with_suffix(".zip.partial")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, source in files.items():
            relative = PurePosixPath(name)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or ":" in name
                or "\\" in name
                or name == "manifest.json"
            ):
                raise ValueError(f"unsafe archive name: {name}")
            archive.write(source, name)
        archive.writestr("manifest.json", json.dumps(manifest, allow_nan=False))
    temporary.replace(path)
    return Path(path)
