import json
import zipfile
from pathlib import Path


def write_media_library(folder: Path, entries: list[dict], name: str = 'media_library.zip') -> Path:
    """Writes a media library zip with a v2 description sibling. Main entries become
    real zip members; variant entries carry a `variant` block."""
    path = folder/name
    with zipfile.ZipFile(path, 'w') as zp:
        for entry in entries:
            zp.writestr(entry['file_id'], b'image-bytes')
    (folder/(name + '.description.json')).write_text(json.dumps(entries))
    return path
