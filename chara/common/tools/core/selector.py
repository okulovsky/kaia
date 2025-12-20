from .interfaces import IDrawable
from typing import Callable, Any

class Selector:
    def __init__(self, selector: Callable[[IDrawable], Any]|str):
        self.selector = selector

    def __call__(self, argument: IDrawable) -> Any:
        if isinstance(self.selector, str):
            return argument.metadata.get(self.selector, None)
        else:
            return self.selector(argument)

