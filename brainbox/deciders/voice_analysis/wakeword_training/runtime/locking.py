"""Validate settings before entering a cached Chara call."""

from contextlib import contextmanager
from pathlib import Path

from .io import read_json, write_json


@contextmanager
def run_lock(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    # OS-managed advisory lock is released even after process termination.
    stream = (folder / ".wakeword.lock").open("a+b")
    try:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if __import__("os").name == "nt":
            import msvcrt

            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        stream.close()
        raise RuntimeError("another wakeword process is using this output folder")
    try:
        yield
    finally:
        stream.seek(0)
        if __import__("os").name == "nt":
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def check_settings(folder, settings):
    folder = Path(folder)
    path = folder / "settings.json"
    expected = settings.canonical()
    if path.exists():
        if read_json(path) != expected:
            raise ValueError("settings changed; choose a new output folder")
    elif any(p.name != ".wakeword.lock" for p in folder.iterdir()):
        raise ValueError(
            "output contains data without settings; choose a new output folder"
        )
    else:
        write_json(path, expected)
