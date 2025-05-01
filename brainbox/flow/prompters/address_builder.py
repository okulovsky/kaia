from typing import *
from .address import DefaultElement, Address
from uuid import uuid4


class AddressBuilderGC:
    cache: dict[str, Address] = {}
    operators: dict[str, Any] = {}


RESERVED_FIELDS = {
    '_address_builder_stored_address',
    '_address_builder_uuid',
    '__str__',
    '__truediv__',
}

class AddressBuilder:
    def __init__(self, address: Address|None = None):
        self._address_builder_uuid = 'id'+str(uuid4()).replace('-','')
        self._address_builder_stored_address = address if address is not None else Address()
        AddressBuilderGC.cache[self._address_builder_uuid] = self._address_builder_stored_address

    def __str__(self):
        return f'<<#{self._address_builder_uuid}>>'

    def __getattribute__(self, item):
        if item in RESERVED_FIELDS:
            return super().__getattribute__(item)
        return AddressBuilder(self._address_builder_stored_address.append(DefaultElement(item)))

    def __truediv__(self, other):
        AddressBuilderGC.operators[self._address_builder_uuid] = other
        return self.__str__()
