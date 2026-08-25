from ....common import Node
from ..basics import BlockType, NodeData, NodeType, Separation, TextCache
from .id_to_node import IdToNode
from .node_factory import node_folder

_ALLOWED_CHILDREN = {
    NodeType.Folder: (NodeType.Folder, NodeType.File),
    NodeType.File: (NodeType.Section,),
    NodeType.Section: (NodeType.Block,),
    NodeType.Block: (),
}


def _name(node: Node) -> str:
    data = node[NodeData]
    return f'{data.node_type}/{data.id}'


def _check_expansion(node: Node, problems: list[str]):
    if not node.has(TextCache):
        problems.append(f'{_name(node)} has no TextCache')
        return
    if len(node.children) == 0:
        problems.append(f'{_name(node)} has a text but no children')
        return
    expanded = '\n'.join(child[TextCache].text for child in node.children)
    if expanded != node[TextCache].text:
        problems.append(f'{_name(node)} does not expand into its children: {len(expanded)} chars against {len(node[TextCache].text)}')


def _check_separation(node: Node, problems: list[str]):
    if not node.has(Separation):
        problems.append(f'{_name(node)} has no Separation')
        return
    ids = [child[NodeData].id for child in node.children]
    if node[Separation].ids != ids:
        problems.append(f'{_name(node)} separation does not follow its children')


def verify(data, max_block_length: int|None = None) -> list[str]:
    """
    Every invariant the rest of the system relies on, checked against a live
    tree: that a file expands into exactly its own text through its sections
    and their blocks, that the separations and root[IdToNode] agree with the
    children, that node types nest as they should, and that the caches the
    tree was built from are on disk. Returns the problems found - an empty
    list means the tree is sound.

    Cheap enough to run after every synchronization; the point is that it can
    be pointed at the real corpus, not only at test fixtures.
    """
    problems: list[str] = []
    root = data.root
    id_to_node = root[IdToNode]
    seen: dict[str, Node] = {}

    for node in root.descendants():
        node_data = node[NodeData]
        name = _name(node)

        if node_data.id in seen and seen[node_data.id] is not node:
            problems.append(f'{name} shares its id with another node')
        seen[node_data.id] = node

        if id_to_node.get(node_data.id) is not node:
            problems.append(f'{name} is not registered in IdToNode')

        if node_data.simhash is None:
            problems.append(f'{name} has no simhash')

        allowed = _ALLOWED_CHILDREN[node_data.node_type]
        for child in node.children:
            if child[NodeData].node_type not in allowed:
                problems.append(f'{name} has a child of type {child[NodeData].node_type}')

        folder = node_folder(data, node_data.node_type, node_data.id)
        if not folder.is_dir():
            problems.append(f'{name} has no cache folder')

        if node_data.node_type == NodeType.File:
            if node.has(TextCache) or node.has(Separation):
                _check_expansion(node, problems)
                _check_separation(node, problems)
        elif node_data.node_type == NodeType.Section:
            _check_expansion(node, problems)
            _check_separation(node, problems)
        elif node_data.node_type == NodeType.Block:
            if not node.has(TextCache):
                problems.append(f'{name} has no TextCache')
            elif len(node[TextCache].paragraphs) == 0:
                problems.append(f'{name} is empty')
            elif (max_block_length is not None
                  and node_data.block_type == BlockType.Text
                  and node[TextCache].paragraphs.length > max_block_length
                  and len(node[TextCache].paragraphs) > 1):
                problems.append(f'{name} is {node[TextCache].paragraphs.length} chars long, over the limit, and could be cut')
            if node_data.block_type not in (BlockType.Caption, BlockType.Plan, BlockType.Text):
                problems.append(f'{name} has no block type')
            if len(node.children) > 0:
                problems.append(f'{name} has children')

    for id, node in id_to_node.items():
        if node is not root and node not in seen.values():
            problems.append(f'IdToNode holds {id}, which is not in the tree')

    return problems


def verify_against_loader(data) -> list[str]:
    """
    verify(), plus the check that closes the loop with the outside world: what
    the loader says a file's text is, is what the tree expands back into.
    """
    problems = verify(data)
    id_to_node = data.root[IdToNode]
    for id in data.settings.loader.get_ids():
        node = id_to_node.get(id)
        if node is None:
            problems.append(f'file {id} is in the loader but not in the tree')
            continue
        text = data.settings.loader.get_text(id)
        if node[TextCache].text != text:
            problems.append(f'file {id} does not hold the text the loader reports')
        expanded = '\n'.join(
            '\n'.join(block[TextCache].text for block in section.children)
            for section in node.children
        )
        if expanded != text:
            problems.append(f'file {id} does not expand into the text the loader reports')
    return problems
