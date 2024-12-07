from enum import Enum


class PromptEnum(Enum):
    def __str__(self):
        if isinstance(self.value, str):
            return self.value
        return self.name.replace('_',' ')

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.__str__() >= other.__str__()
        raise NotImplementedError()

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.__str__() > other.__str__()
        raise NotImplementedError()

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.__str__() <= other.__str__()
        raise NotImplementedError()

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.__str__() < other.__str__()
        raise NotImplementedError()