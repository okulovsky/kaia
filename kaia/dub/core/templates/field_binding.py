from ..structures import Dub, ToStrDub, IDubBinding
from .inline_binding import IInlineBinding

class Address:
    def __init__(self, *address:str):
        for i,c in enumerate(address):
            if not isinstance(c, str):
                raise ValueError(f"Error in address at index {i}: expected str, but was {c}")
        self.address = address

    def _one_step(self, obj, address_element):
        if hasattr(obj, address_element):
            return getattr(obj, address_element)
        return obj[address_element]


    def get(self, obj):
        for element in self.address:
            obj = self._one_step(obj, element)
        return obj

    def desc(self):
        return '/'.join(self.address)

    def append(self, value: str):
        new_address = self.address+(value,)
        return Address(*new_address)

    def is_empty(self):
        return len(self.address) == 0

class FieldDubBinding(IDubBinding):
    def __init__(self, name: str, address: Address, dub: Dub):
        self._name = name
        self._address = address
        self._dub = dub

    @property
    def type(self):
        return self._dub

    @property
    def name(self):
        return self._name

    def get_consumed_keys(self) -> tuple[str, ...]:
        return (self._address.address[0],)

    @property
    def produces_value(self):
        return False

    def get_value_to_consume(self, d):
        return self._address.get(d)


    def set_produced_value(self, value, d) -> None:
        pass



class FieldBinding(IInlineBinding):
    def __init__(self,
                 address: Address|None = None,
                 dub: Dub = None
                 ):
        if dub is None:
            dub = ToStrDub()
        if address is None:
            address = Address()
        self._address = address
        self._dub = dub

    def get_hash(self) -> str:
        return 'FieldBinding//'+self._address.desc()

    def get_dub(self) -> Dub | IDubBinding:
        if self._address.is_empty():
            raise ValueError("Cannot use empty address for a dub")
        return FieldDubBinding(self._address.address[0], self._address, self._dub)


