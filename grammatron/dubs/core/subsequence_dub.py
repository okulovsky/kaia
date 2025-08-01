from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import uuid4
from foundation_kaia.prompters import AddressBuilderGC, Address
from .dub import IDub, DubParameters
from typing import Any, TYPE_CHECKING


class ISubSequenceDub(IDub, ABC):
    def __str__(self):
        id = str(uuid4())
        AddressBuilderGC.record(
            AddressBuilderGC.Dimension.address,
            id,
            Address('*')
        )
        AddressBuilderGC.record(
            AddressBuilderGC.Dimension.misc,
            id,
            self
        )
        return f'<<{id}>>'

    @abstractmethod
    def get_sequence(self) -> tuple['ISubSequenceDub',...]|None:
        pass

    def get_leaves(self) -> tuple['ISubSequenceDub',...]:
        sequence = self.get_sequence()
        if sequence is None:
            return (self,)
        return tuple(element for subs in sequence for element in subs.get_leaves())

    def _convolute_to_dictionary(self, values: dict[tuple[str,...], Any], parameters: DubParameters, target: dict[str, Any]):
        result = self.convolute_values(values, parameters)
        if not isinstance(result, dict):
            raise ValueError("If not overriden, `convolute_values` is expected to return a dict")
        for key, value in result.items():
            target[key] = value

    @abstractmethod
    def _get_human_readable_representation_internal(self, parameters: DubParameters):
        pass

    def get_human_readable_representation(self, parameters: DubParameters|None = None):
        return self._get_human_readable_representation_internal(self.adjust_parameters(parameters))




