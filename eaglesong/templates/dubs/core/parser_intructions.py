from typing import *
from dataclasses import dataclass, field

class IParserInstruction:
    pass

@dataclass
class ConstantParserInstruction(IParserInstruction):
    value: str

@dataclass
class VariableParserInstruction(IParserInstruction):
    variable_name: tuple[str,...]


@dataclass
class SequenceParserInstruction(IParserInstruction):
    sequence: tuple[IParserInstruction,...]

@dataclass
class UnionParserInstruction(IParserInstruction):
    union: tuple[IParserInstruction,...]

@dataclass
class IterationParserInstruction(IParserInstruction):
    iterated: 'SubdomainInstruction'

@dataclass
class SubdomainInstruction(IParserInstruction):
    variable_name: tuple[str, ...]
    subdomain: 'ParserData'

@dataclass
class VariableInfo:
    string_values_to_value: dict[str,Any]

@dataclass
class ParserData:
    root: IParserInstruction
    variables: dict[tuple[str,...], VariableInfo]|None = None



