from abc import ABC, abstractmethod
from ..prompters import Address, AddressBuilder
from copy import deepcopy

class IApplicator(ABC):
    @abstractmethod
    def apply(self, obj, data_to_apply) -> list:
        pass


class SimpleApplicator(IApplicator):
    def __init__(self, address: Address|AddressBuilder|str):
        self.address = Address(address)

    def apply(self, obj, data_to_apply) -> list:
        obj = deepcopy(obj)
        self.address.set(obj, data_to_apply)
        return [obj]

class ListExpansionApplicator(IApplicator):
    def __init__(self, address: Address|AddressBuilder, index_address: Address|AddressBuilder|None = None):
        self.address = Address(address)
        self.index_address = Address(index_address) if index_address is not None else None


    def apply(self, obj, data_to_apply) -> list:
        try:
            data_to_apply = list(data_to_apply)
        except:
            raise ValueError(f"data_to_apply must be convertible to list")
        result = []
        sap = SimpleApplicator(self.address)
        index_sap = None if self.index_address is None else SimpleApplicator(self.index_address)
        for index, item in enumerate(data_to_apply):
            mod = sap.apply(obj, item)
            if index_sap is not None:
                mod = index_sap.apply(mod[0], index)
            result.append(mod[0])
        return result

