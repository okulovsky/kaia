from .address_builder import AddressBuilder
from typing import TypeVar, Generic

T = TypeVar('T')

class Referrer(Generic[T]):
    @property
    def ref(self) -> T:
        return AddressBuilder()
