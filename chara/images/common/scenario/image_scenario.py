from abc import ABC, abstractmethod
from brainbox.deciders.images.comfyui.workflows import IWorkflow
from chara.common import ICase
from dataclasses import fields

class IImageScenario(ABC, ICase):
    @abstractmethod
    def to_workflow(self) -> IWorkflow:
        pass


def assemble_tags(*parts) -> str|None:
    result = []
    for p in parts:
        if p is None:
            continue
        elif isinstance(p, str):
            result.append(p)
        else:
            for s in p:
                result.append(s)
    if len(result) == 0:
        return None
    return ', '.join(result)


def convert_to_lists(dataclass_object):
    for field in fields(dataclass_object):
        value = getattr(dataclass_object, field.name)
        if isinstance(value, str):
            setattr(dataclass_object, field.name, [value])
