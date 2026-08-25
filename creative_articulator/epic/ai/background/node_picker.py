from ....common import Node, FileNodeStorage
from ...model import NodeData, hamming_distance
from dataclasses import dataclass

@dataclass
class BackgroundConfirmation:
    simhash: int

@dataclass
class BackgroundStatus:
    confirmation_missing: bool = False
    simhash_changed: bool = False
    distance: int|None = None
    children_synced: bool = True

    @property
    def sync_required(self) -> bool:
        return self.confirmation_missing or self.simhash_changed

    @property
    def sync_required_and_possible(self) -> bool:
        return self.sync_required and self.children_synced


def _node_status(node: Node):
    if not node.has(BackgroundConfirmation):
        return BackgroundStatus(confirmation_missing=True)
    if node[NodeData].simhash == node[BackgroundConfirmation].simhash:
        return BackgroundStatus()
    distance = hamming_distance(
        node[NodeData].simhash,
        node[BackgroundConfirmation].simhash
    )
    return BackgroundStatus(simhash_changed=True, distance = distance)


def _assign_statuses(root: Node):
    nodes = list(root.descendants())
    nodes.reverse()
    for node in nodes:
        node.storage(FileNodeStorage).memory_only(BackgroundStatus)
        status = _node_status(node)
        if len(node.children) > 0:
            for child in node.children:
                if not child.has(BackgroundStatus):
                    raise ValueError("Should not happen")
                if child[BackgroundStatus].sync_required:
                    status.children_synced = False
                    break
        node[BackgroundStatus] = status


def find_node_to_process(root: Node) -> Node|None:
    """
    assign statuses, then pick the node that should and can be synced, and of all such nodes, pick the one that has confirmation_missing, if no such, pick one with highest distance
    """
    _assign_statuses(root)
    candidates = [node for node in root.descendants() if node[BackgroundStatus].sync_required_and_possible]
    if not candidates:
        return None
    missing = [node for node in candidates if node[BackgroundStatus].confirmation_missing]
    if missing:
        return missing[0]
    return max(candidates, key=lambda node: node[BackgroundStatus].distance)