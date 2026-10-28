from pathlib import Path
from datetime import datetime
import threading
from typing import TypeVar, Callable, Any
from .chara_stack import CharaStack, CharaStackItem
from .chara_caller import CharaCaller

T = TypeVar('T')
from .validate import restore_consistency
from .result_handling import find_result, read_result
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
        return read_result(self.item.folder)

    @property
    def has_result(self) -> bool:
        return find_result(self.item.folder) is not None


class CharaInstance:
    def __init__(self):
        self.thread_to_stack: dict[int, CharaStack] = dict()
        self.Apis = CharaApis.default()

    def _stack(self) -> CharaStack:
        id = threading.get_ident()
        if id not in self.thread_to_stack:
            raise ValueError("Chara was not initialized in this thread")
        return self.thread_to_stack[id]


    def start(self, working_folder: Path):
        restore_consistency(working_folder)
        id = threading.get_ident()
        if id in self.thread_to_stack and not self._stack().exited:
            raise ValueError("Another chara process is already in progress in this thread")
        self.thread_to_stack[id] = CharaStack(working_folder)

    @staticmethod
    def _find_last_run_folder(root: Path, prefix: str) -> Path|None:
        candidates = []
        if root.is_dir():
            for folder in root.iterdir():
                if not folder.is_dir() or not folder.name.startswith(prefix):
                    continue
                try:
                    candidates.append((datetime.fromisoformat(folder.name[len(prefix):]), folder))
                except ValueError:
                    continue
        if len(candidates) == 0:
            return None
        return max(candidates)[1]

    def start_or_resume(self, root: Path, prefix: str) -> Path:
        """Resumes the last `<prefix><timestamp>` run folder under `root` if it has no result
        yet, and starts a new one otherwise. Returns the folder."""
        folder = self._find_last_run_folder(root, prefix)
        if folder is None or self.from_folder(folder).has_result:
            folder = root / (prefix + datetime.now().isoformat())
        self.start(folder)
        return folder

    def call(self, function: T, alternative_name: str|None = None) -> T:
        self._stack().check_exited()
        return CharaCaller(self._stack(), function, alternative_name)

    def phase(self, func=None):
        def decorator(f: Callable):
            return CharaCaller(self._stack(), f, name=f.__name__)()

        if callable(func):
            return decorator(func)
        else:
            return decorator

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

    def from_folder(self, folder: Path) -> CharaFolder:
        return CharaFolder(CharaStackItem(folder,'',0,0))





Chara: CharaInstance = CharaInstance()