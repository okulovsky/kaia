from typing import  TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class AvatarMessageSet(Generic[T]):
    missing_id: bool
    missing_session: bool
    messages: list[T]
