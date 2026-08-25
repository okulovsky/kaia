from ....common import Node


class IdToNode(dict[str, Node]):
    """
    Maps every id (file, folder, section or block) to its live Node, so
    update(id, ...) and friends don't have to walk the tree to resolve one.
    Lives on root[IdToNode] rather than as a field on CreativeArticulatorData,
    so it travels with the tree itself.
    """
