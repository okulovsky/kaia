from pathlib import Path
import threading
from typing import TypeVar, Callable, Any
from .chara_stack import CharaStack, CharaStackItem
from .chara_caller import CharaCaller

T = TypeVar('T')
from .invalidate import invalidate
from .result_handling import find_result, read_result, FileResult, ResultType
from .apis import CharaApis


class CharaFolder:
    def __init__(self, item: CharaStackItem):
        self.item = item

    @property
    def folder(self) -> Path:
        return self.item.folder

    @property
    def result(self) -> Any:
        result_file = find_result(self.item.folder)
        if result_file is None:
            raise ValueError(f"The folder {self.item.folder} does not have the result file")
        return read_result(result_file)

    @property
    def has_result(self) -> bool:
        return find_result(self.item.folder) is not None


class CharaInstance:
    def __init__(self):
        self.thread_to_stack: dict[int, CharaStack] = dict()
        self.FileResult = FileResult
        self.ResultType = ResultType
        self.Apis = CharaApis.default()

    def _stack(self) -> CharaStack:
        id = threading.get_ident()
        if id not in self.thread_to_stack:
            raise ValueError("Chara was not initialized in this thread")
        return self.thread_to_stack[id]


    def start(self, working_folder: Path):
        id = threading.get_ident()
        if id in self.thread_to_stack and not self._stack().exited:
            raise ValueError("Another chara process is already in progress in this thread")
        self.thread_to_stack[id] = CharaStack(working_folder)

    def call(self, function: T, alternative_name: str|None = None) -> T:
        self._stack().check_exited()
        return CharaCaller(self._stack(), function)

    def phase(self, func_or_result_type=None):
        def decorator(func: Callable, result_type: ResultType = ResultType.Pickle):
            return CharaCaller(self._stack(), func, name=func.__name__, result_type=result_type)()

        if callable(func_or_result_type):
            return decorator(func_or_result_type)
        else:
            rt = func_or_result_type if func_or_result_type is not None else ResultType.Pickle
            return lambda func: decorator(func, rt)

    @property
    def current(self) -> CharaFolder:
        stack = self._stack()
        stack.check_exited()
        return CharaFolder(stack.stack[-1])

    @property
    def previous(self) -> CharaFolder:
        stack = self._stack()
        if stack.last_exited is not None:
            return CharaFolder(stack.last_exited)
        raise ValueError("No exits were made yet in this Chara process")

    def invalidate_down(self, path: Path|str):
        self._invalidate(path, True)

    def invalidate_self(self, path: Path|str):
        self._invalidate(path, False)

    def _invalidate(self, path: Path|str, down: bool):
        path = Path(path)
        root = self._stack().root
        invalidate(path, root, down)




Chara: CharaInstance = CharaInstance()