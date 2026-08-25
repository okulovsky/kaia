import os
from pathlib import Path
from typing import TYPE_CHECKING

from ....common import Node, FileNodeStorage
from ..basics import NodeData, NodeType

if TYPE_CHECKING:
    from .creative_articulator_data import CreativeArticulatorData


def create_cached_node(data: 'CreativeArticulatorData', folder: Path, node_type: NodeType, id: str, title: str|None = None, block_type: int|None = None) -> Node:
    os.makedirs(folder, exist_ok=True)
    node = Node(FileNodeStorage(folder, data.settings.namespaces))
    if node.has(NodeData):
        with node.session(NodeData):
            existing = node[NodeData]
            existing.node_type = node_type
            existing.id = id
            existing.title = title
            existing.block_type = block_type
    else:
        node[NodeData] = NodeData(node_type, id, title, None, block_type)
    return node


def load_cached_node(data: 'CreativeArticulatorData', folder: Path) -> Node:
    return Node(FileNodeStorage(folder, data.settings.namespaces))


def node_folder(data: 'CreativeArticulatorData', node_type: NodeType, id: str) -> Path:
    locations = data.settings.locations
    if node_type == NodeType.Folder:
        return locations.folder_caches / id
    if node_type == NodeType.File:
        return locations.file_caches / id
    if node_type == NodeType.Section:
        return locations.section_caches / id
    return locations.block_caches / id
