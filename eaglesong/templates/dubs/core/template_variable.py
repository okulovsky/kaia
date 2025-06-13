from typing import *
from dataclasses import dataclass, field
from .dub import IDub, IGrammarAdoptionDub
from .to_str_dub import ToStrDub
from uuid import uuid4
from foundation_kaia.prompters import AddressBuilderGC, Address

@dataclass
class TemplateVariableAssignment:
    variable: 'TemplateVariable'
    value: Any

@dataclass
class TemplateVariable:
    name: str|None
    dub: IDub = field(default_factory=ToStrDub)
    description: str|None = None

    def __post_init__(self):
        if self.name is None:
            if not isinstance(self.dub, IGrammarAdoptionDub):
                raise ValueError("Only grammar adoption dubs are allowed to be anonymous variables")

    def __str__(self):
        id = str(uuid4())
        AddressBuilderGC.record(
            AddressBuilderGC.Dimension.address,
            id,
            Address(self.name)
        )
        AddressBuilderGC.record(
            AddressBuilderGC.Dimension.misc,
            id,
            self
        )
        return f'<<{id}>>'

    def rename(self, name: str) -> 'TemplateVariable':
        return TemplateVariable(
            name,
            self.dub,
            self.description
        )

    def assign(self, value):
        return TemplateVariableAssignment(self, value)

