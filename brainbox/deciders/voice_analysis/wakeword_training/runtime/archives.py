"""Bounded, allowlisted and deterministic ZIP transport."""

import os
import stat
import zipfile
from pathlib import Path
from uuid import uuid4

BUDGET = 2 * 1024**3


def safe_name(name):
    parts = name.replace("\\", "/").split("/")
    if (
        not name
        or any(p in ("", ".", "..") for p in parts)
        or ":" in name
        or "\\" in name
    ):
        raise ValueError("unsafe archive path")
    return name


def write_archive(path, files, budget=BUDGET):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    total = 0
    try:
        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True
        ) as archive:
            for name, source in sorted(files.items()):
                safe_name(name)
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                with (
                    Path(source).open("rb") as incoming,
                    archive.open(info, "w", force_zip64=True) as outgoing,
                ):
                    for chunk in iter(lambda: incoming.read(1024 * 1024), b""):
                        total += len(chunk)
                        if total > budget:
                            raise ValueError("expanded archive exceeds budget")
                        outgoing.write(chunk)
        if temporary.stat().st_size > budget:
            raise ValueError("archive exceeds budget")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def extract_archive(path, destination, allowed, budget=BUDGET):
    path = Path(path)
    destination = Path(destination)
    if path.stat().st_size > budget:
        raise ValueError("archive exceeds budget")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [safe_name(i.filename) for i in infos]
        if len(names) != len({n.casefold() for n in names}) or set(names) != set(
            allowed
        ):
            raise ValueError("archive file allowlist mismatch")
        if sum(i.file_size for i in infos) > budget:
            raise ValueError("expanded archive exceeds budget")
        for item in infos:
            mode = item.external_attr >> 16
            if (
                item.flag_bits & 1
                or stat.S_ISLNK(mode)
                or item.is_dir()
                or item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
            ):
                raise ValueError("unsupported archive member")
        destination.mkdir(parents=True, exist_ok=True)
        total = 0
        for item in infos:
            target = destination / item.filename
            if (
                not target.resolve().is_relative_to(destination.resolve())
                or target.exists()
            ):
                raise ValueError("archive would overwrite a file")
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(item) as source, target.open("xb") as output:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    total += len(chunk)
                    if total > budget:
                        raise ValueError("expanded archive exceeds budget")
                    output.write(chunk)
    return destination
