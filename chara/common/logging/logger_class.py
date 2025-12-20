from typing import Callable, Any, TypeVar, Type
from ..cache import ICacheEntity
from .simple import HeaderItem, ILogItem, ExceptionItem, ObjectItem
import pickle
import time
from pathlib import Path

T = TypeVar('T')


class Section:
    def __init__(self, logger: 'Logger', caption: str):
        self._logger = logger
        self._caption = caption

    def __enter__(self):
        self._logger.log(HeaderItem(self._logger.current_level, self._caption))
        self._logger.current_level += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logger.current_level -= 1


class HtmlLogFile:
    def __init__(self, logger: 'Logger', file: Path):
        self._logger = logger
        self._file = file
        self._logger_index: int|None = None

    def __enter__(self):
        self._logger_index = len(self._logger.items)

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self._file, 'w') as file:
            file.write(
                "<!DOCTYPE html>"
                "<html>"
                "<head><meta charset='utf-8'></head>"
                "<body>"
            )
            for item in self._logger.items[self._logger_index:]:
                file.write(item.to_html())
            file.write("</body></html>")


class Logger:
    def __init__(self, on_item: Callable[[ILogItem], None]):
        self.items: list[ILogItem] = []
        self.on_item = on_item
        self.current_level = 0

    def reset(self):
        self.items = []
        self.current_level = 0

    def section(self, caption: str) -> Section:
        return Section(self, caption)

    def log(self, message: Any):
        if not isinstance(message, ILogItem):
            message = ILogItem.create(message)
        self.items.append(message)
        if self.on_item is not None:
            self.on_item(message)

    def html_report(self, file: Path) -> HtmlLogFile:
        return HtmlLogFile(self, file)


    def phase(self,
              cache_entity: ICacheEntity,
              description: str|None = None,
              *,
              allow_unfilled_exit: bool = False):
        caption = cache_entity.name if description is None else description
        log_path = cache_entity.log_path

        def decorator(fn: Callable[[], None]):
            with self.section(caption):
                verb = 'failed'
                if not cache_entity.ready:
                    log_index = len(self.items)
                    begin = time.monotonic()
                    try:
                        fn()
                        if not allow_unfilled_exit and not cache_entity.ready:
                            raise ValueError("Stage doesn't fill up the cache it was created for")
                        verb = 'completed'
                    except Exception as e:
                        self.log(ExceptionItem(e))
                        raise
                    finally:
                        end = time.monotonic()
                        phase_log = self.items[log_index:]
                        try:
                            with open(log_path, 'wb') as stream:
                                pickle.dump(phase_log, stream)
                        except Exception as e:
                            self.log("Can't save phase log to disk")
                        self.log(f"Stage {caption} {verb} in {int(end - begin)} seconds")
                else:
                    self.log("Stage restored from cache")
                    if log_path.is_file():
                        with open(log_path, 'rb') as stream:
                            phase_log = pickle.load(stream)
                            for element in phase_log:
                                self.log(element)

        return decorator

    def get_object(self, cls: Type[T]) -> T:
        for item in reversed(self.items):
            if isinstance(item, ObjectItem) and isinstance(item.object, cls):
                return item.object
        raise ValueError(f"Object of type {T} is not found in logs")


















