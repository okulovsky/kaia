from typing import *
from .template import Template, Dub

def _intents_decorator(_cls):
    for field in vars(_cls):
        obj = getattr(_cls, field)
        if isinstance(obj, Template):
            name = _cls.__module__+'.'+_cls.__name__+'.'+field
            obj.name = name
    return _cls


class DynamicTemplatesCollection:
    def __init__(self, templates: dict[str, Template]):
        self.templates = templates
        for key, value in templates.items():
            setattr(self, key, value)

    def get_templates(self):
        return self.templates.values()




class TemplatesCollection:
    def __init_subclass__(cls, **kwargs):
        return _intents_decorator(cls)

    @classmethod
    def get_templates_as_dict(cls) -> dict[str, Template]:
        result = {}
        for field in vars(cls):
            obj = getattr(cls, field)
            if isinstance(obj, Template):
                result[field] = obj
        return result

    @classmethod
    def get_templates(cls) -> list[Template]:
        return list(cls.get_templates_as_dict().values())


    @classmethod
    def substitute(cls, dubs: Dict[str, Dub]):
        new_templates = {}
        for key, template in cls.get_templates_as_dict().items():
            new_templates[key] = template.substitute(dubs)
        return DynamicTemplatesCollection(new_templates)




