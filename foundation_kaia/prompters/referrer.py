from .address_builder import AddressBuilder
from typing import TypeVar, Generic

T = TypeVar('T')

class Referrer(Generic[T]):
    @property
    def ref(self) -> T:
        return AddressBuilder()

    def list_to_bullet_points(self, bullet_point = '* '):
        def _f(value):
            return '\n'.join(bullet_point+s for s in value)
        return _f



