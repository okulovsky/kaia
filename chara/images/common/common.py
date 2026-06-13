from abc import ABC, abstractmethod
from brainbox.deciders.images.comfyui.workflows import TextToImage
from chara.common import ICase

class IImageScenario(ABC, ICase):
    @abstractmethod
    def to_workflow(self) -> TextToImage:
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