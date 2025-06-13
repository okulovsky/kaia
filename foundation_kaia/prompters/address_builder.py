from typing import *
from .address import DefaultElement, Address
from uuid import uuid4
from enum import IntEnum


class AddressBuilderGC:
    class Dimension(IntEnum):
        address = 0
        operator = 1
        subprompt = 2
        misc = 100

    cache: dict['AddressBuilderGC.Dimension', dict[str,Any]] = {}

    @staticmethod
    def record(dimension: 'AddressBuilderGC.Dimension', id: str, value: Any):
        if dimension not in AddressBuilderGC.cache:
            AddressBuilderGC.cache[dimension] = {}
        AddressBuilderGC.cache[dimension][id] = value

    @staticmethod
    def find(dimension: 'AddressBuilderGC.Dimension', id: str):
        if dimension not in AddressBuilderGC.cache:
            return None
        if id not in AddressBuilderGC.cache[dimension]:
            return None
        return AddressBuilderGC.cache[dimension][id]


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
        AddressBuilderGC.record(
            AddressBuilderGC.Dimension.address,
            self._address_builder_uuid,
            self._address_builder_stored_address
        )

    def __str__(self):
        return f'<<{self._address_builder_uuid}>>'

    def __getattribute__(self, item):
        if item in RESERVED_FIELDS:
            return super().__getattribute__(item)
        return AddressBuilder(self._address_builder_stored_address.append(DefaultElement(item)))

    def __truediv__(self, other):
        AddressBuilderGC.record(
            AddressBuilderGC.Dimension.operator,
            self._address_builder_uuid,
            other
        )
        return self.__str__()

    def __invert__(self):
        AddressBuilderGC.record(
            AddressBuilderGC.Dimension.subprompt,
            self._address_builder_uuid,
            True
        )
        return self.__str__()


