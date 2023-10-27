from typing import *
from .template import Template

def _intents_decorator(_cls):
    for field in vars(_cls):
        obj = getattr(_cls, field)
        if isinstance(obj, Template):
            name = _cls.__module__+'.'+_cls.__name__+'.'+field
            obj.name = name
    return _cls


class TemplatesCollection:
    def __init_subclass__(cls, **kwargs):
        return _intents_decorator(cls)

    @classmethod
    def get_templates(cls) -> List[Template]:
        result = []
        for field in vars(cls):
            obj = getattr(cls, field)
            if isinstance(obj, Template):
                result.append(obj)
        return result
