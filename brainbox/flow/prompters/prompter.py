from typing import *
from .abstract_prompter import IPrompter, T, Generic
from .address import Address
from .address_builder import AddressBuilderGC
import re
from uuid import uuid4


def _parse(template: str):
    parts = re.split('(<<[^>]+>>)', template)
    addresses = {}
    operators = {}
    template_parts = []
    for part in parts:
        if part.startswith('<<') and part.endswith('>>'):
            uid = part[2:-2]
            if len(uid) == 0:
                raise ValueError("Expected address or pre-generated address between << and >> ")
            if uid[0] == '#':
                addresses[uid] = AddressBuilderGC.cache[uid[1:]]
                if uid in AddressBuilderGC.operators:
                    operators[uid] = AddressBuilderGC.operators[uid]
                template_parts.append('{' + uid + '}')
            else:
                address = Address.parse(uid)
                uid = str(uuid4())
                addresses[uid] = address
                template_parts.append('{' + uid + '}')
        else:
            template_parts.append(part)

    return template_parts, addresses, operators


class Prompter(IPrompter[T], Generic[T]):
    def __init__(self, template: str):
        self.template_parts, self.field_to_address, self.field_to_formatter = _parse(template)

    def __call__(self, obj: T) -> str:
        values = {}
        for key, address in self.field_to_address.items():
            o = address.get(obj)
            if key in self.field_to_formatter:
                o = self.field_to_formatter[key](o)
            values[key] = o
        return ''.join(self.template_parts).format(**values)

    def to_readable_string(self):
        result = []
        for part in self.template_parts:
            if part.startswith('{') and part.endswith('}'):
                addr: Address = self.field_to_address[part[1:-1]]
                result.append(f'<<{addr.__str__()}>>')
            else:
                result.append(part)
        return ''.join(result)

