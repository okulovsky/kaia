import logging
import shutil
from pathlib import Path

from ....common import FileNodeStorage
from ..basics import NodeData, Separation, TextCache

logger = logging.getLogger(__name__)


def _subfolders(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(path for path in root.iterdir() if path.is_dir())


def _read(data, folder: Path, key: type):
    """
    The value stored under `key` in this cache folder, or None if it isn't
    there or can't be read back. A half-written or hand-edited file is thus
    indistinguishable from a missing one - both mean "this cache is not
    usable", which is all the caller needs to decide.
    """
    storage = FileNodeStorage(folder, data.settings.namespaces)
    if not storage.has(key):
        return None
    try:
        return storage.get(key)
    except Exception:
        logger.warning(f'Cannot read {key.__name__} from {folder}', exc_info=True)
        return None


def _delete(folder: Path, reason: str, deleted: list[Path]):
    logger.info(f'Deleting inconsistent cache {folder}: {reason}')
    shutil.rmtree(folder)
    deleted.append(folder)


def restore_consistency(data) -> list[Path]:
    """
    Brings the cache folders back to a state the rest of the code can trust,
    by deleting every folder that isn't wholly usable. Runs before the tree is
    built from disk (see CreativeArticulatorData._load), so nothing downstream
    has to cope with a half-present cache.

    A cache folder is always written complete, so an incomplete one means an
    intervention from outside between runs - typically a file deleted by hand
    to force a recomputation. Nothing is salvaged from a damaged file: it is
    deleted whole, and the next synchronize() refetches its text from the
    loader and splits it from scratch. What counts as damaged:

    - a block folder without both NodeData and TextCache;
    - a section folder without NodeData, TextCache and Separation, or whose
      separation names a block that just failed the check above;
    - a file folder without NodeData; or holding a text but no separation of
      it, or the reverse (the two are written together, so one without the
      other means a run died in between and the file would otherwise never be
      separated again); or whose separation names a section that failed its
      own check;
    - a folder-node folder without NodeData.

    Section and block folders that no surviving separation names are deleted
    too. Those are unreachable - separation ids are random guids, so nothing
    can ever name them again - and this is the only thing that collects them
    (synchronize() drops such nodes from the tree but leaves the folders).

    Returns the deleted folders, for logging and tests.
    """
    locations = data.settings.locations
    deleted: list[Path] = []

    intact_blocks = set()
    for folder in _subfolders(locations.block_caches):
        if _read(data, folder, NodeData) is None:
            _delete(folder, 'block has no NodeData', deleted)
        elif _read(data, folder, TextCache) is None:
            _delete(folder, 'block has no TextCache', deleted)
        else:
            intact_blocks.add(folder.name)

    intact_sections = set()
    for folder in _subfolders(locations.section_caches):
        separation = _read(data, folder, Separation)
        if _read(data, folder, NodeData) is None:
            _delete(folder, 'section has no NodeData', deleted)
        elif _read(data, folder, TextCache) is None:
            _delete(folder, 'section has no TextCache', deleted)
        elif separation is None:
            _delete(folder, 'section has no Separation', deleted)
        elif not set(separation.ids) <= intact_blocks:
            _delete(folder, 'section is separated into blocks that are damaged or gone', deleted)
        else:
            intact_sections.add(folder.name)

    referenced_sections = set()
    for folder in _subfolders(locations.file_caches):
        separation = _read(data, folder, Separation)
        has_text = _read(data, folder, TextCache) is not None
        if _read(data, folder, NodeData) is None:
            _delete(folder, 'file has no NodeData', deleted)
        elif (separation is not None) != has_text:
            _delete(folder, 'file has a text but no separation of it, or the reverse', deleted)
        elif separation is not None and not set(separation.ids) <= intact_sections:
            _delete(folder, 'file is separated into sections that are damaged or gone', deleted)
        elif separation is not None:
            referenced_sections |= set(separation.ids)

    referenced_blocks = set()
    for folder in _subfolders(locations.section_caches):
        if folder.name not in referenced_sections:
            _delete(folder, 'section belongs to no file', deleted)
        else:
            referenced_blocks |= set(_read(data, folder, Separation).ids)

    for folder in _subfolders(locations.block_caches):
        if folder.name not in referenced_blocks:
            _delete(folder, 'block belongs to no section', deleted)

    for folder in _subfolders(locations.folder_caches):
        if _read(data, folder, NodeData) is None:
            _delete(folder, 'folder has no NodeData', deleted)

    return deleted
