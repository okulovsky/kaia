import uuid
from datetime import datetime, timezone

from creative_articulator.common import Node
from creative_articulator.epic.model import (
    BlockType, ILoader, NodeData, NodeType, ParagraphArray, TextCache
)
from creative_articulator.epic.model.algorithms import TextFragment


def paragraphs(text: str) -> ParagraphArray:
    return ParagraphArray.parse(text)


def fragment(text: str, payload=None) -> TextFragment:
    return TextFragment(paragraphs(text), payload)


def block_fragment(text: str, block_type: int = BlockType.Text, id: str|None = None) -> TextFragment[NodeData]:
    data = NodeData(NodeType.Block, id or uuid.uuid4().hex, None, None, block_type)
    return TextFragment(paragraphs(text), data)


def cached_node(node_type: int, id: str, text: str, title: str|None = None, block_type: int|None = None) -> Node:
    node = Node()
    node[NodeData] = NodeData(node_type, id, title, None, block_type)
    node[TextCache] = TextCache(paragraphs(text), datetime.now(timezone.utc))
    return node


def node_with_children(children: list[Node], node_type: int = NodeType.Section) -> Node:
    node = Node()
    node[NodeData] = NodeData(node_type, 'parent')
    for child in children:
        node.append(child)
    return node


def blocks_node(blocks: list[tuple[str, str, int]]) -> Node:
    children = [cached_node(NodeType.Block, id, text, None, block_type) for id, text, block_type in blocks]
    return node_with_children(children)


def sections_node(sections: list[tuple[str, str]]) -> Node:
    children = [cached_node(NodeType.Section, id, text) for id, text in sections]
    return node_with_children(children, NodeType.File)


def joined(fragments) -> str:
    return '\n'.join(texts(fragments))


def ids(fragments) -> list[str]:
    return [f.payload.id for f in fragments]


def texts(fragments) -> list[str]:
    return [f.paragraphs.text for f in fragments]


class FakeLoader(ILoader):
    """
    Test double for ILoader: the id list and each id's text/modification-time
    are configurable, and every call is recorded, so tests can assert not just
    on results but on whether a (potentially expensive) fetch actually
    happened.
    """

    def __init__(self):
        self.texts: dict[str, str] = {}
        self.modified: dict[str, datetime] = {}
        self.text_calls: list[str] = []
        self.modified_calls: list[str] = []

    def set_text(self, id: str, text: str, modified: datetime|None = None) -> None:
        self.texts[id] = text
        self.modified[id] = modified or datetime.now(timezone.utc)

    def get_ids(self) -> list[str]:
        return list(self.texts)

    def get_text(self, id: str) -> str:
        self.text_calls.append(id)
        return self.texts[id]

    def get_modified(self, id: str) -> datetime:
        self.modified_calls.append(id)
        return self.modified[id]
