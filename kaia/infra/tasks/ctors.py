from typing import *
import inspect

def _load_module(part):
    mod = __import__(part)
    subpath = part.split('.')
    for s in subpath[1:]:
        methods = inspect.getmembers(mod)
        new_mods = [obj for name, obj in methods if name == s]
        if len(new_mods) == 0:
            raise ValueError('Path {0} is not found in module {1}'.format(s, mod))
        if len(new_mods) > 1:
            raise ValueError('More than two objects at path {0} are found in module {1}'.format(s, mod))
        mod = new_mods[0]
    return mod

def _load_class(module, path):
    result = module
    path = path.split('.')
    for p in path:
        result = getattr(result, p)
    return result

class Ctor:
    def __init__(self, class_path: str, args = None, kwargs = None):
        self.class_path = class_path
        self.args = args
        if self.args is None:
            self.args = ()
        self.kwargs = kwargs
        if self.kwargs is None:
            self.kwargs = {}

    def __call__(self):
        module_name, class_name = self.class_path.split(':')
        module = _load_module(module_name)
        ctor = _load_class(module, class_name)
        return ctor(*self.args, **self.kwargs)

