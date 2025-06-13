import inspect
from dataclasses import dataclass
from collections import OrderedDict

@dataclass
class SignatureProcessor:
    mandatory: tuple[str,...]
    optional: tuple[str,...]
    open: bool

    def to_kwargs_only(self, *args, **kwargs):
        all = self.mandatory + self.optional
        if len(args) > len(all):
            raise ValueError(f"args has {len(args)} arguments, while there are only {len(all)} arguments")
        result = OrderedDict()
        for i, arg in enumerate(args):
            name = all[i]
            if name in kwargs:
                raise ValueError(f"Args at index {i} conflicts with kwargs {name}")
            result[name] = arg

        for key, value in kwargs.items():
            result[key] = value

        mandatory_seen = set()
        for key in result:
            if key in self.mandatory:
                mandatory_seen.add(key)
            elif key in self.optional:
                pass
            else:
                if not open:
                    raise ValueError(f"Argument `{key}` is not in fields, and the signature is not open")

        if len(mandatory_seen) < len(self.mandatory):
            not_seen = ", ".join([f'`{c}`' for c in self.mandatory if c not in mandatory_seen])
            raise TypeError(f"Not all mandatory arguments are provided: missing {not_seen}")

        return result

    @staticmethod
    def from_signature(method):
        signature = inspect.signature(method)
        mandatory = list()
        optional = list()
        open = False
        for i,(p,v) in enumerate(signature.parameters.items()):
            if i == 0 and v.name=='self':
                continue
            if v.kind == inspect.Parameter.VAR_KEYWORD:
                open = True
            else:
                if v.default == inspect._empty:
                    mandatory.append(v.name)
                else:
                    optional.append(v.name)
        return SignatureProcessor(tuple(mandatory), tuple(optional), open)