import shutil
from pathlib import Path
from .result_handling import find_result, remove_result
from .logger_definition import logger


def _get_numeric_children(folder: Path) -> dict[str, Path]:
    result = {}
    for item in folder.iterdir():
        if item.is_dir():
            try:
                int(item.name.split('-')[0])
                result[item.name] = item
            except (ValueError, IndexError):
                pass
    return result


def _read_cache(folder: Path) -> list[str] | None:
    cache_file = folder / '.cache'
    if not cache_file.exists():
        return None
    return [line.strip() for line in cache_file.read_text().splitlines() if line.strip()]


def find_first_inconsistency(root: Path) -> Path | None:
    return _find_recursive(root, root)


def fix_inconsistency(folder: Path, root: Path):
    logger.info(f"Removing result from {folder}")
    remove_result(folder)
    if folder == root:
        return
    folder_index = int(folder.name.split('-')[0])
    for name, path in _get_numeric_children(folder.parent).items():
        if int(name.split('-')[0]) > folder_index:
            logger.info(f"Removing folder {path}")
            shutil.rmtree(path)


def restore_consistency(root: Path):
    if not root.exists():
        return
    path = find_first_inconsistency(root)
    if path is None:
        logger.info(f"No inconsistencies at {root}")
        return
    logger.info(f"Inconsistency found at {path}")
    current = path
    while True:
        fix_inconsistency(current, root)
        if current == root:
            break
        current = current.parent


def _find_recursive(folder: Path, root: Path) -> Path | None:
    expected = _read_cache(folder)

    if expected is None: #Backward compatibility
        numeric_children = _get_numeric_children(folder)
        if numeric_children and find_result(folder) is not None:
            raise ValueError(
                f"Cache folder '{folder.relative_to(root)}' has a result and child "
                f"directories but no .cache file. Delete the result file to force re-run."
            )
    else:
        for child_name in expected:
            child_path = folder / child_name
            if child_path.exists():
                found = _find_recursive(child_path, root)
                if found is not None:
                    return found
            else:
                return child_path

    if not find_result(folder):
        return folder

    return None

