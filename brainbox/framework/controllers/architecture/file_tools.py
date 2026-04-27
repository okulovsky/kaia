from foundation_kaia.marshalling import FileLike, FileLikeHandler
from ...common.streaming import StreamingStorage
from pathlib import Path

def brainbox_file_like_to_bytes_iterable(file_like: FileLike, cache_folder: Path):
    if isinstance(file_like, str) and '/' not in file_like:
        return StreamingStorage(cache_folder).read(file_like)
    return FileLikeHandler.to_bytes_iterable(file_like)

