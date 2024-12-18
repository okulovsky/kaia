from typing import *
import inspect
from dataclasses import dataclass, field

@dataclass
class ArgumentsValidator:
    mandatory: set[str]
    optional: set[str]
    open: bool
    arguments_sequence: tuple[str,...]
    mandatory_seen: set[str] = field(default_factory=set)
    seen: set[str] = field(default_factory=set)


    def _validate(self, name):
        if name in self.seen:
            raise ValueError(f"Argument {name} occurs two times (check both `dependencies` and `arguments`)")
        if name in self.mandatory:
            self.mandatory_seen.add(name)
        elif name in self.optional:
            pass
        elif not self.open:
            raise ValueError(f"Unexpected argument {name}")

    def _end_validation(self):
        if len(self.mandatory) != len(self.mandatory_seen):
            raise ValueError(f"The following arguments are missing: "+",".join(self.mandatory-self.mandatory_seen))

    def validate(self, parameters: Iterable[str]):
        for v in parameters:
            self._validate(v)
        self._end_validation()


    @staticmethod
    def from_signature(method):
        signature = inspect.signature(method)
        mandatory = set()
        optional = set()
        open = False
        sequence = []
        for i,(p,v) in enumerate(signature.parameters.items()):
            if i == 0 and v.name=='self':
                continue
            if v.kind == inspect.Parameter.VAR_KEYWORD:
                open = True
            else:
                sequence.append(v.name)
                if v.default == inspect._empty:
                    mandatory.add(v.name)
                else:
                    optional.add(v.name)
        return ArgumentsValidator(mandatory, optional, open, tuple(sequence))