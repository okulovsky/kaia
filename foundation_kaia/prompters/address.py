from abc import ABC, abstractmethod

class IAddressElement(ABC):
    @abstractmethod
    def get(self, obj):
        pass

    @abstractmethod
    def set(self, obj, value):
        pass

    @staticmethod
    def translate(element) -> 'IAddressElement':
        if isinstance(element, IAddressElement):
            return element
        return DefaultElement(element)



class DefaultElement(IAddressElement):
    def __init__(self, element):
        self.element = element

    def get(self, obj):
        if isinstance(self.element, str) and hasattr(obj, self.element):
            return getattr(obj, self.element)
        if hasattr(obj, '__getitem__'):
            getitem = getattr(obj, '__getitem__')
            if callable(getitem):
                return getitem(self.element)
        raise ValueError(f"Obj {obj} cannot be addressed with {self.element}")

    def set(self, obj, value):
        if hasattr(obj, '__setitem__'):
            setitem = getattr(obj, '__setitem__')
            if callable(setitem):
                setitem(obj, self.element, value)
                return
        if isinstance(self.element, str):
            setattr(obj, self.element, value)
            return
        raise ValueError(f"Obj {obj} cannot be set with address `{self.element}`")

    def __str__(self):
        if isinstance(self.element, str):
            return self.element
        return f'[{self.element}]'


class Address:
    def __init__(self, *address):
        from .address_builder import AddressBuilder
        if len(address) == 1:
            if isinstance(address[0], AddressBuilder):
                self.address = address[0]._address_builder_stored_address.address
            elif isinstance(address[0], Address):
                self.address = address[0].address
            else:
                self.address = (IAddressElement.translate(address[0]), )
        else:
            self.address: tuple[IAddressElement,...] = tuple(IAddressElement.translate(a) for a in address)

    def get(self, obj):
        result = obj
        for index, element in enumerate(self.address):
            try:
                result = element.get(result)
            except Exception as exc:
                raise ValueError(f"Address {self} failed at {index} for object\n{obj}") from exc
        return result

    def set(self, obj, value):
        obj = self.pop().get(obj)
        self.address[-1].set(obj, value)

    def append(self, value: str|IAddressElement):
        if isinstance(value, str):
            value= IAddressElement.translate(value)
        elif isinstance(value, IAddressElement):
            pass
        else:
            raise ValueError("Expected string or IAddressElement")
        return Address(*(self.address+(value,)))

    def pop(self) -> 'Address':
        if len(self.address) == 0:
            raise ValueError("Can't pop from empty address")
        return Address(*self.address[:-1])

    def is_empty(self):
        return len(self.address) == 0

    def __str__(self):
        return '.'.join(str(a) for a in self.address)

    @staticmethod
    def parse(s: str):
        parts = s.split('.')
        parts = [DefaultElement(e) for e in parts]
        return Address(*parts)
