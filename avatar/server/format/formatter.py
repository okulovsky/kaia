from abc import abstractmethod, ABC
from typing import Union, Type, Tuple

class Thrower:
    def __init__(self, path: 'SerializationPath', word: str):
        self.prefix = f'Serialization error, {word} at {path.base}'

    def exc(self, msg: str):
        raise ValueError(f"{self.prefix}: {msg}")

    def type(self, value, _type):
        raise TypeError(f"{self.prefix}: `{_type}` is expected, but was value of type `{type(value)}`:\n{value}")

    def check_type(self, value, _type: Union[Type,Tuple[Type,...]]):
        if not isinstance(value, _type):
            self.type(value, _type)




class SerializationPath:
    def __init__(self, base='/'):
        self.base = base

    def append(self, value):
        return SerializationPath(self.base+str(value)+'/')

    @property
    def to_json(self) -> Thrower:
        return Thrower(self, 'to_json')

    @property
    def from_json(self) -> Thrower:
        return Thrower(self, 'from_json')


class IFormatter(ABC):
    @property
    def not_null(self) -> bool:
        if not hasattr(self,'_notnull'):
            return True
        return self._notnull

    @not_null.setter
    def not_null(self, value: bool):
        self._notnull = value


    def to_json(self, value, path: SerializationPath):
        if value is None:
            if self.not_null:
                path.to_json.exc(f'None is unexpected')
            return None
        return self._to_json(value, path)

    def from_json(self, value, path: SerializationPath):
        if value is None:
            if self.not_null:
                path.from_json.exc(f'None is unexpected')
            return None
        return self._from_json(value, path)

    @abstractmethod
    def _to_json(self, value, path: SerializationPath):
        pass

    @abstractmethod
    def _from_json(self, value, path: SerializationPath):
        pass



