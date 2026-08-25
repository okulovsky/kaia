from __future__ import annotations

from contextlib import contextmanager
from typing import Optional, Type, TypeVar, Iterable
from .node_storage import INodeStorage
from .memory_node_storage import MemoryNodeStorage
from .tracker import ITracker, NodeChange
from dataclasses import dataclass



@dataclass
class LinearizedNode:
    level: int
    node: 'Node'

T = TypeVar('T')

class FieldAccessor:
    def __init__(self, node: 'Node'):
        self._node = node

    def __getattribute__(self, item):
        node = object.__getattribute__(self, '_node')
        item = item.replace('_', '').lower()
        for key, value in node._storage.items():
            if key.__name__.lower().endswith(item):
                return value
        raise AttributeError(item)


class Node:
    def __init__(self, storage: INodeStorage | None = None):
        if storage is None:
            storage = MemoryNodeStorage()
        self._storage: INodeStorage = storage
        self._parent: Optional[Node] = None
        self._children: list[Node] = []

    def __getitem__(self, item: Type[T]) -> T:
        self.ensure(item)
        return self._storage.get(item)

    def __setitem__(self, key: Type[T], value: T) -> None:
        self._storage.set(key, value)
        self._track(NodeChange.Kind.CHANGED, key)

    def attach(self, value, custom_type: type = None) -> Node:
        if custom_type is None:
            custom_type = type(value)
        self[custom_type] = value
        return self

    def get(self, key: Type[T], default: T | None = None) -> T | None:
        if not self._storage.has(key):
            return default
        return self._storage.get(key)

    def has(self, key: Type[T]) -> bool:
        return self._storage.has(key)

    def delete(self, key: type) -> None:
        self._storage.delete(key)
        self._track(NodeChange.Kind.KEY_REMOVED, key)

    def ensure(self, key: type):
        if not self._storage.has(key):
            self[key] = key()

    def commit(self, key: type):
        self._storage.commit(key)
        self._track(NodeChange.Kind.CHANGED, key)

    def rollback(self, key: type):
        self._storage.rollback(key)

    @contextmanager
    def session(self, key: type):
        try:
            yield
            self.commit(key)
        except Exception:
            self.rollback(key)

    def storage(self, tp: Type[T] = INodeStorage) -> T:
        if not isinstance(self._storage, tp):
            raise ValueError(f"Expected the storage to be of type {tp}, but was {type(self._storage)}")
        return self._storage


    @property
    def parent(self) -> Optional[Node]:
        return self._parent

    @property
    def root(self) -> Node:
        n = self
        while True:
            if n.parent is None:
                return n
            n = n.parent

    @property
    def index(self) -> int:
        if self._parent is None:
            return 0
        return self._parent._children.index(self)

    @property
    def children(self) -> tuple[Node, ...]:
        return tuple(self._children)

    @property
    def fields(self) -> FieldAccessor:
        return FieldAccessor(self)

    def append(self, child: Node) -> Node:
        child._detach()
        child._parent = self
        self._children.append(child)
        child._track(NodeChange.Kind.ADDED)
        return child

    def insert(self, index: int, child: Node) -> Node:
        child._detach()
        child._parent = self
        self._children.insert(index, child)
        child._track(NodeChange.Kind.ADDED)
        return child

    def remove(self, child: Node) -> Node:
        child._detach()
        return child

    def remove_at(self, index: int) -> Node:
        return self.remove(self._children[index])

    def ancestors(self, include_self: bool = False) -> tuple[Node, ...]:
        result = []
        node = self if include_self else self._parent
        while node is not None:
            result.append(node)
            node = node._parent
        return tuple(reversed(result))

    def left_siblings(self) -> tuple[Node, ...]:
        if self._parent is None:
            return ()
        siblings = self._parent._children
        return tuple(siblings[:siblings.index(self)])

    def right_siblings(self) -> tuple[Node, ...]:
        if self._parent is None:
            return ()
        siblings = self._parent._children
        return tuple(siblings[siblings.index(self) + 1:])

    def siblings(self) -> tuple[Node, ...]:
        return self.left_siblings() + self.right_siblings()

    def left_excerpt(self, include_self: bool = True, include_parents: bool = True) -> tuple[LinearizedNode, ...]:
        return tuple(self._left_excerpt(include_self, include_parents, 0))

    def _left_excerpt(self, include_this: bool, include_parents: bool, level: int) -> Iterable[LinearizedNode]:
        if self._parent is not None:
            yield from self._parent._left_excerpt(include_parents, include_parents, level - 1)
        for sibling in self.left_siblings():
            yield LinearizedNode(level=level, node=sibling)
        if include_this:
            yield LinearizedNode(level=level, node=self)

    def right_excerpt(self, include_self: bool = True, include_parents: bool = True) -> tuple[LinearizedNode, ...]:
        return tuple(self._right_excerpt(include_self, include_parents, 0))

    def _right_excerpt(self, include_this: bool, include_parents: bool, level: int) -> Iterable[LinearizedNode]:
        if include_this:
            yield LinearizedNode(level=level, node=self)
        for sibling in self.right_siblings():
            yield LinearizedNode(level=level, node=sibling)
        if self._parent is not None:
            yield from self._parent._right_excerpt(include_parents, include_parents, level - 1)

    def descendants(self, include_self: bool = False) -> Iterable[Node]:
        if include_self:
            yield self
        yield from (e.node for e in self._descendants_recursive(0))

    def linearize_descendants(self) -> Iterable[LinearizedNode]:
        yield from self._descendants_recursive(0)

    def _descendants_recursive(self, level: int) -> Iterable[LinearizedNode]:
        for child in self._children:
            yield LinearizedNode(level=level, node=child)
            yield from child._descendants_recursive(level + 1)

    def _detach(self):
        if self._parent is not None:
            self._track(NodeChange.Kind.REMOVED)
            self._parent._children.remove(self)
            self._parent = None

    def _track(self, kind: NodeChange.Kind, key: type | None = None):
        root = self.root
        if root.has(ITracker):
            root[ITracker].on_change(NodeChange(kind, self, key))

