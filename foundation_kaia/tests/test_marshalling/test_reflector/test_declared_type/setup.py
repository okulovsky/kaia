from typing import Generic, TypeVar

T = TypeVar('T')
T1 = TypeVar('T1')

class Basic(Generic[T]):
    ...

class Defining(Basic[str]):
    ...

class Passthrough(Basic[T], Generic[T]):
    ...

class Switching(Passthrough[list[T]], Generic[T]):
    ...

class Switching2(Switching[tuple[T,...]], Generic[T]):
    ...

class Double(Generic[T, T1]):
    ...

class DoubleToSingleWithSwitch(Double[list[int], T], Generic[T]):
    ...