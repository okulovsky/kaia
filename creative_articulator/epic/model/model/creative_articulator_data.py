from typing import Iterable

from ....common import Node
from dataclasses import dataclass, field
from ..algorithms import Algorithms
from ..basics import NodeData, NodeType, TextCache, simhash
from .id_to_node import IdToNode
from .loader import ILoader
from .locations import CreativeArticulatorLocations


def _compute_node_simhash(node: Node) -> int:
    if node[NodeData].node_type == NodeType.Block:
        return simhash(node[TextCache].text)
    return simhash(d[TextCache].text for d in node.descendants() if d[NodeData].node_type == NodeType.Block)


@dataclass
class CreativeArticulatorSettings:
    locations: CreativeArticulatorLocations
    namespaces: tuple[str, ...]
    loader: ILoader
    algorithms: Algorithms = field(default_factory=Algorithms)


@dataclass
class CreativeArticulatorData:
    root: Node
    settings: CreativeArticulatorSettings

    def _refresh_simhashes(self, affected: Iterable[Node]):
        affected = list(affected)
        for node in self.root.descendants():
            if node[NodeData].simhash is None:
                affected.append(node)
        affected_ancestors = []
        for node in affected:
            for parent in node.ancestors():
                if parent is not self.root:
                    affected_ancestors.append(parent)
        ids = set(node[NodeData].id for node in affected_ancestors+affected)
        for id in ids:
            node = self.root[IdToNode].get(id)
            if node is None or node is self.root:
                continue
            with node.session(NodeData):
                node[NodeData].simhash = _compute_node_simhash(node)

    def _load(self):
        from .consistency import restore_consistency
        from .structure import load
        from .separation import restore
        # Before anything reads the caches: a folder damaged from outside is
        # deleted whole here, so the tree is built from caches that are either
        # wholly there or not there at all.
        restore_consistency(self)
        load(self)
        for item in tuple(self.root.descendants()):
            if item[NodeData].node_type == NodeType.File:
                restore(self, item)

    def load(self):
        self._load()
        self._refresh_simhashes([])

    def synchronize(self):
        """
        Reconciles the whole tree against the loader: which files exist, what
        their text is now, and how it splits into sections and blocks. The set
        of files comes from the loader itself (ILoader.get_ids), so this needs
        nothing from the caller and can also be used to recover - a file whose
        cache was damaged from outside was deleted by _load, and is refetched
        and separated from scratch right here.
        """
        from .structure import synchronize_structure, synchronize_caches
        from .separation import synchronize
        ids = self.settings.loader.get_ids()
        synchronize_structure(self, ids)
        self._load()
        updated_nodes = synchronize_caches(self, ids)
        separated = []
        for node in updated_nodes:
            separated.extend(synchronize(self, node))
        self._refresh_simhashes(updated_nodes+separated)

    def update(self, id: str, text: str):
        from .structure import update
        from .separation import synchronize
        node = update(self, id, text)
        self._refresh_simhashes([node]+synchronize(self, node))
