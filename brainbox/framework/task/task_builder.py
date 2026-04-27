import copy

from .task import BrainBoxTask, BrainBoxTaskOptionals
from foundation_kaia.marshalling import Signature, JSON, Serializer
from dataclasses import dataclass
from typing import Self


@dataclass
class TaskBuilderSignature:
    decider: str
    argument_to_ordering_token_position: dict[str, int]
    signature: Signature

@dataclass
class Dependency:
    id: str

class TaskBuilderEndpoint:
    def __init__(self,
                 signature: TaskBuilderSignature,
                 optionals: BrainBoxTaskOptionals,
                 after_others: list[str|BrainBoxTask]
                 ):
        self.signature = signature
        self.optionals = optionals
        self.after_others = after_others

    def __call__(self, *args, **kwargs):
        arguments: dict[str, JSON] = {}
        dependencies: dict[str, str|BrainBoxTask] = {}
        ordered_token_parts: dict[int, str] = {}

        name_to_value = self.signature.signature.assign_parameters_to_names(*args, **kwargs)
        ctx = Serializer.Context()
        for name, value in name_to_value.items():
            if isinstance(value, BrainBoxTask):
                dependencies[name] = value
            elif isinstance(value, Dependency):
                dependencies[name] = value.id
            else:
                arguments[name] = value
                if name in self.signature.argument_to_ordering_token_position:
                    ordered_token_parts[self.signature.argument_to_ordering_token_position[name]] = str(value)
        if len(ordered_token_parts) > 0:
            ordering_token = '/'.join(z[1] for z in sorted(ordered_token_parts.items(), key=lambda z: z[0]))
        else:
            ordering_token = ''

        return BrainBoxTask(
            self.signature.decider,
            self.signature.signature.name,
            arguments,
            dependencies,
            self.after_others,
            ordering_token,
            self.optionals
        )



class TaskBuilder:
    def __getattribute__(self, item):
        d = super().__getattribute__('__dict__')
        signatures = d.get('_signatures', {})
        if item in signatures:
            return TaskBuilderEndpoint(signatures[item], d['_optionals'], d['_after_others'])
        return super().__getattribute__(item)

    def after(self, *others: str|BrainBoxTask) -> Self:
        cp = copy.copy(self)
        cp._after_others = others
        return cp


