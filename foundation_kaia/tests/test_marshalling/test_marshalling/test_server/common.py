import time
from pathlib import Path
from collections.abc import Iterable

CHUNKS = [b'a' * 100, b'b' * 100, b'c' * 100]
POLL_TIMEOUT = 0.5
POLL_INTERVAL = 0.005


def _wait_for_size(path: Path, expected_size: int):
    """Polls until the file contains at least expected_size bytes."""
    deadline = time.monotonic() + POLL_TIMEOUT
    while time.monotonic() < deadline:
        if path.exists() and path.stat().st_size >= expected_size:
            return
        time.sleep(POLL_INTERVAL)
    actual = path.stat().st_size if path.exists() else 0
    raise AssertionError(
        f"Signal file {path.name}: expected size >= {expected_size}, got {actual} "
        f"(timeout {POLL_TIMEOUT}s)"
    )


def sender(signal_file: Path):
    """Yields each chunk only after the previous one has been fully written to the file."""
    total = 0
    for chunk in CHUNKS:
        yield chunk
        total += len(chunk)
        _wait_for_size(signal_file, total)


def receiver(signal_file: Path, stream: Iterable[bytes]):
    """Reads from stream and writes each chunk to the signal file."""
    with open(signal_file, 'wb') as f:
        for chunk in stream:
            f.write(chunk)
            f.flush()
