import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ....common import Node
from ..basics import NodeType, TextCache
from .id_to_node import IdToNode
from .node_factory import create_cached_node


@dataclass
class _StructureLine:
    title: str
    id: str|None  # parsed "| <id>" suffix; None means it's a folder line
    level: int
    children: list['_StructureLine'] = field(default_factory=list)


def _parse_line(line: str) -> _StructureLine:
    level = len(line) - len(line.lstrip(' '))
    content = line.lstrip(' ')
    if '|' in content:
        title, id = content.rsplit('|', 1)
        return _StructureLine(title.rstrip(), id.strip(), level)
    return _StructureLine(content.strip(), None, level)


def _parse_structure(text: str) -> list[_StructureLine]:
    """Indentation encodes nesting: a line is nested under the closest
    preceding line with a strictly lower indentation level."""
    roots: list[_StructureLine] = []
    stack: list[_StructureLine] = []
    for raw_line in text.split('\n'):
        if raw_line.strip() == '':
            continue
        line = _parse_line(raw_line)
        while stack and stack[-1].level >= line.level:
            stack.pop()
        while stack and stack[-1].id is not None:
            stack.pop()
        if stack:
            stack[-1].children.append(line)
        else:
            roots.append(line)
        stack.append(line)
    return roots


def _folder_id(title: str, child_ids: list[str]) -> str:
    if not child_ids:
        return hashlib.sha256(title.encode('utf-8')).hexdigest()
    return hashlib.sha256('|'.join(child_ids).encode('utf-8')).hexdigest()


def _build_node(data, id_to_node: IdToNode, line: _StructureLine) -> tuple[Node, str]:
    if line.id is not None:
        node = create_cached_node(data, data.settings.locations.file_caches / line.id, NodeType.File, line.id, line.title)
        id_to_node[line.id] = node
        return node, line.id

    children = [_build_node(data, id_to_node, child) for child in line.children]
    folder_id = _folder_id(line.title, [child_id for _, child_id in children])
    node = create_cached_node(data, data.settings.locations.folder_caches / folder_id, NodeType.Folder, folder_id, line.title)
    for child_node, _ in children:
        node.append(child_node)
    id_to_node[folder_id] = node
    return node, folder_id


def load(data):
    """
    Parses data.settings.locations.structure (title, and " | <id>" for file
    lines; indentation encodes nesting) into a tree rooted at data.root - a
    synthetic Node that isn't itself an entry in structure.txt. Every node
    gets a NodeData and a FileNodeStorage-backed cache directory (file_caches
    for files, folder_caches for folders, the latter keyed by a hash of its
    children's ids, or of its own title if it has none). root[IdToNode] is
    rebuilt from scratch to map every file/folder id to its live Node (section
    and block ids are added later, by restore()/synchronize()).

    data.root itself is reused (its children are rebuilt, not the object): a
    caller that keeps a reference to data.root across a reload should keep
    seeing the same object, since load() runs on every synchronize() call.
    """
    from .creative_articulator_data import CreativeArticulatorData
    root = data.root
    for child in root.children:
        root.remove(child)
    root[CreativeArticulatorData] = data

    id_to_node = IdToNode()
    root[IdToNode] = id_to_node
    structure_file = data.settings.locations.structure
    text = structure_file.read_text(encoding='utf-8') if structure_file.is_file() else ''
    for line in _parse_structure(text):
        node, _ = _build_node(data, id_to_node, line)
        root.append(node)


def _remove_missing(lines: list[_StructureLine], ids: set[str]) -> list[_StructureLine]:
    kept = []
    for line in lines:
        if line.id is not None and line.id not in ids:
            continue
        line.children = _remove_missing(line.children, ids)
        kept.append(line)
    return kept


def _collect_file_ids(lines: list[_StructureLine]) -> set[str]:
    ids = set()
    for line in lines:
        if line.id is not None:
            ids.add(line.id)
        ids |= _collect_file_ids(line.children)
    return ids


def _title_from_text(text: str, id: str) -> str:
    for raw_line in text.split('\n'):
        stripped = raw_line.strip()
        if stripped:
            return stripped
    return id


def _serialize(lines: list[_StructureLine], level: int = 0) -> list[str]:
    # 4 spaces per level: the editor reads depth as spaces // 4 (see
    # structure_drive_storage.INDENT_WIDTH), so anything else flattens its tree.
    rendered = []
    for line in lines:
        prefix = '    ' * level
        rendered.append(f'{prefix}{line.title} | {line.id}' if line.id is not None else f'{prefix}{line.title}')
        rendered.extend(_serialize(line.children, level + 1))
    return rendered


def synchronize_structure(data, ids: list[str]):
    """
    Reconciles data.settings.locations.structure against `ids`: a file line
    whose id isn't in `ids` is dropped (along with any now-orphaned
    sub-structure), and an id with no matching file line is appended as a new
    top-level entry. A brand-new id has no title anywhere else, so its text is
    fetched right here (data.settings.loader.get_text) just to derive one
    from its first non-blank line; ids that already have a line are untouched
    and cost no fetch.

    This only rewrites the structure.txt text; it doesn't touch data.root or
    root[IdToNode]; the caller (CreativeArticulatorData.synchronize) always
    calls load() right after, which rebuilds both from scratch.
    """
    structure_file = data.settings.locations.structure
    text = structure_file.read_text(encoding='utf-8') if structure_file.is_file() else ''
    lines = _parse_structure(text)

    lines = _remove_missing(lines, set(ids))

    existing_ids = _collect_file_ids(lines)
    for id in ids:
        if id not in existing_ids:
            title = _title_from_text(data.settings.loader.get_text(id), id)
            lines.append(_StructureLine(title, id, 0))

    rendered = _serialize(lines)
    structure_file.write_text('\n'.join(rendered) + ('\n' if rendered else ''), encoding='utf-8')


def synchronize_caches(data, ids: list[str]) -> list[Node]:
    """
    For each id, checks data.settings.loader.get_modified(id) - a cheap
    metadata-only call - against the file-node's cached TextCache.updated.
    Only when that cache is missing or older does it pay for the actual
    content fetch (data.settings.loader.get_text(id)), timestamped with the
    fetched modification time (not wall-clock time, so re-running this
    without a source change is a no-op). Returns the nodes that were
    refreshed.
    """
    id_to_node = data.root[IdToNode]
    updated_nodes = []
    for id in ids:
        node = id_to_node.get(id)
        if node is None:
            continue
        # Aware UTC, like every timestamp in the tree: a loader that reports
        # a naive local time (or none at all) must not turn into a TypeError
        # against the cached TextCache.updated on the very next line.
        modified = data.settings.loader.get_modified(id).astimezone(timezone.utc)
        if node.has(TextCache) and node[TextCache].updated >= modified:
            continue
        node[TextCache] = TextCache.from_text(data.settings.loader.get_text(id), modified)
        updated_nodes.append(node)
    return updated_nodes


def update(data, id: str, text: str) -> Node:
    """Directly sets a node's text (no loader involved) and returns it."""
    node = data.root[IdToNode][id]
    node[TextCache] = TextCache.from_text(text, datetime.now(timezone.utc))
    return node
