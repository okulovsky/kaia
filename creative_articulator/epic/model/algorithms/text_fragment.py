from __future__ import annotations
from dataclasses import dataclass
from ..basics import ParagraphArray, NodeData
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass
class Match(Generic[T]):
    matched_with: TextFragment[T]
    match: float

@dataclass
class TextFragment(Generic[T]):
    paragraphs: ParagraphArray
    payload: T
    match: Match[T]|None = None
