from pathlib import Path
from ...common import File

def _dump(file, cache_folder: Path):
    if isinstance(file, File):
        with open(cache_folder / file.name, 'wb') as stream:
            stream.write(file.content)
            file.content = None
        return file.name
    else:
        return file


def file_postprocess(obj, cache_folder: Path):
    if isinstance(obj, File):
        return _dump(obj, cache_folder)
    elif isinstance(obj, tuple):
        return tuple(_dump(f, cache_folder) for f in obj)
    elif isinstance(obj, list):
        return [_dump(f, cache_folder) for f in obj]
    elif isinstance(obj, dict):
        return {key: _dump(value, cache_folder) for key, value in obj.items()}
    else:
        return obj