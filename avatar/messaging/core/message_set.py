from typing import TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class AvatarMessageSetElement(Generic[T]):
    session: str
    message: T


@dataclass
class AvatarMessageSet(Generic[T]):
    missing_id: bool
    messages: list[AvatarMessageSetElement[T]]
