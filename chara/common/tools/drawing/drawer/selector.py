from typing import Any, Callable
from foundation_kaia.prompters import Address

class Selector:
    def __init__(self, element):
        self.lambda_getter: Callable|None = None
        self.address: Address|None = None

        if callable(element):
            self.lambda_getter = element
        elif isinstance(element, str):
            self.address = Address.parse(element)
        else:
            self.address = Address(element)

    def get(self, obj: Any):
        if self.lambda_getter is not None:
            return self.lambda_getter(obj)
        else:
            return self.address.get(obj)