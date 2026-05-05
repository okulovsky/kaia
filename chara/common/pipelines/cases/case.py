from typing import TypeVar


class ICase:
    @property
    def error(self) -> str|None:
        if not hasattr(self, '_error'):
            return None
        return self._error

    @error.setter
    def error(self, value: str|None) -> None:
        self._error = value


TCase = TypeVar('TCase', bound=ICase)