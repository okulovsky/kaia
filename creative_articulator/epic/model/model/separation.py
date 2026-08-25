from datetime import datetime, timezone

from ....common import Node
from ..basics import NodeData, NodeType, ParagraphArray, Separation, TextCache
from .id_to_node import IdToNode
from .node_factory import create_cached_node, load_cached_node, node_folder


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require(node: Node, key: type, folder) -> None:
    if not node.has(key):
        raise ValueError(
            f"Cache '{folder}' has no {key.__name__}, but it is a part of a separation. "
            f"restore_consistency should have deleted the owning file before it got here."
        )


def restore(data, node: Node):
    """
    The node must be of the file type. Reads node[Separation] (if present) and
    appends a section-type child node for each id in it, each of them in turn
    restored from its own Separation into block-type children, all backed by
    the persistent per-id cache folders and registered in root[IdToNode]. If
    there is no Separation yet, the node is new and is left with no children.

    A section's and a block's cache must hold their text: an id naming a cache
    that doesn't is not something to work around here, because
    restore_consistency runs first and deletes any file whose sections or
    blocks are damaged. Reaching this point means that pass and this one
    disagree, so it raises rather than building a damaged tree.
    """
    if not node.has(Separation):
        return
    id_to_node = node.root[IdToNode]
    for section_id in node[Separation].ids:
        folder = node_folder(data, NodeType.Section, section_id)
        section = load_cached_node(data, folder)
        _require(section, NodeData, folder)
        _require(section, TextCache, folder)
        _require(section, Separation, folder)
        id_to_node[section_id] = section
        node.append(section)
        for block_id in section[Separation].ids:
            block_folder = node_folder(data, NodeType.Block, block_id)
            block = load_cached_node(data, block_folder)
            _require(block, NodeData, block_folder)
            _require(block, TextCache, block_folder)
            id_to_node[block_id] = block
            section.append(block)


def _drop(node: Node, id_to_node: IdToNode):
    for descendant in tuple(node.descendants(include_self=True)):
        id_to_node.pop(descendant[NodeData].id, None)
    node.parent.remove(node)


def _reorder(node: Node, children: list[Node], id_to_node: IdToNode):
    for stale in set(node.children) - set(children):
        _drop(stale, id_to_node)
    for index, child in enumerate(children):
        node.insert(index, child)
    node[Separation] = Separation([child[NodeData].id for child in children])


def _set_text(node: Node, paragraphs: ParagraphArray) -> bool:
    if node.has(TextCache) and node[TextCache].text == paragraphs.text:
        return False
    node[TextCache] = TextCache(paragraphs, _now())
    return True


def _synchronize_blocks(data, section: Node, id_to_node: IdToNode) -> list[Node]:
    fragments = data.settings.algorithms.final_section_to_blocks(section[TextCache].paragraphs, section)
    existing = {child[NodeData].id: child for child in section.children}

    changed: list[Node] = []
    blocks: list[Node] = []
    for fragment in fragments:
        id = fragment.payload.id
        block = existing.get(id)
        if block is None:
            block = create_cached_node(
                data,
                node_folder(data, NodeType.Block, id),
                NodeType.Block,
                id,
                None,
                fragment.payload.block_type
            )
            _set_text(block, fragment.paragraphs)
            changed.append(block)
        else:
            if block[NodeData].block_type != fragment.payload.block_type:
                with block.session(NodeData):
                    block[NodeData].block_type = fragment.payload.block_type
            if _set_text(block, fragment.paragraphs):
                changed.append(block)
        id_to_node[id] = block
        blocks.append(block)

    _reorder(section, blocks, id_to_node)
    return changed


def synchronize(data, node: Node) -> list[Node]:
    """
    In this node - a file node - the new text is stored in node[TextCache].

    node may already have a previous version of the text, processed into
    section-node children (in the order of node[Separation].ids), each of them
    processed into block-node children the same way. The new text is split
    into sections and blocks by data.settings.algorithms, which collates them
    against the previous version and decides which of them are the old ones,
    edited (they keep their id, and with it their downstream stats) and which
    are brand new (fresh random guid). A section or block nobody was matched
    to is dropped from the tree, and its entry in root[IdToNode] removed (its
    on-disk cache folder is left alone; since ids are random guids, not
    content-derived, identical text reappearing later will not find it again
    and gets a new id).

    The children on both levels are reordered to match the new text, and the
    Separation of the file and of every section is updated to the resulting id
    sequences.

    Returns the list of section- and block-nodes that are new or whose content
    changed.
    """
    id_to_node = node.root[IdToNode]
    fragments = data.settings.algorithms.final_file_to_sections(node[TextCache].paragraphs, node)
    existing = {child[NodeData].id: child for child in node.children}

    changed: list[Node] = []
    sections: list[Node] = []
    for fragment in fragments:
        id = fragment.payload.id
        section = existing.get(id)
        if section is None:
            section = create_cached_node(
                data,
                node_folder(data, NodeType.Section, id),
                NodeType.Section,
                id,
                fragment.payload.title
            )
            _set_text(section, fragment.paragraphs)
            changed.append(section)
        else:
            if section[NodeData].title != fragment.payload.title:
                with section.session(NodeData):
                    section[NodeData].title = fragment.payload.title
            if _set_text(section, fragment.paragraphs):
                changed.append(section)
        id_to_node[id] = section
        changed.extend(_synchronize_blocks(data, section, id_to_node))
        sections.append(section)

    _reorder(node, sections, id_to_node)
    return changed
