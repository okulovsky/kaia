from dataclasses import dataclass
from typing import ClassVar

class NodeType:
    Folder = 0
    File = 1
    Section = 2
    Block = 3


class BlockType:
    Caption = 0
    Plan = 1
    Text = 2

@dataclass
class NodeData:
    node_type: NodeType
    # Same id used as this node's cache folder name and as the key it's
    # registered under in root[IdToNode] - stored here too so a Node can
    # answer "what's my own id" without a reverse lookup.
    id: str
    title: str|None = None
    # Locality-sensitive hash of this node's own text plus every
    # descendant's (see simhash.py): close content produces close hashes,
    # unlike a cryptographic hash. None until a load()/synchronize()/update()
    # pass computes it - distinct from an actual hash of 0 (e.g. empty text).
    simhash: int|None = None
    block_type: BlockType|None = None

    Type: ClassVar = NodeType


