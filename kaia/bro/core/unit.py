from abc import ABC, abstractmethod
from .space import ISpace
from ...infra.comm import IMessenger

class IUnit(ABC):
    def get_name(self):
        return type(self).__name__

    @abstractmethod
    def run(self, space: ISpace, messenger: IMessenger):
        pass


class UnitOverCallable(IUnit):
    def __init__(self, obj):
        self.callable = obj
        name = type(obj).__name__
        if name == 'function':
            name = obj.__name__
        self.name = name

    def get_name(self):
        return self.name

    def run(self, space: ISpace, messenger: IMessenger):
        self.callable(space)


class GenericUnit(IUnit):
    def __init__(self, obj):
        if isinstance(obj, IUnit):
            self.inner = obj
        else:
            self.inner = UnitOverCallable(obj)

    def get_name(self):
        return self.inner.get_name()

    def run(self, space: ISpace, messenger: IMessenger):
        self.inner.run(space, messenger)
