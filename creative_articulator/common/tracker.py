from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from .node import Node


class ChangeKind(Enum):
    ADDED = 'added'
    REMOVED = 'removed'
    CHANGED = 'changed'
    KEY_REMOVED = 'key_removed'


@dataclass
class NodeChange:
    kind: ChangeKind
    node: Node
    key: Optional[type] = None

    Kind: ClassVar = ChangeKind


class ITracker(ABC):
    Change = NodeChange

    @abstractmethod
    def on_change(self, change: NodeChange) -> None:
        pass
