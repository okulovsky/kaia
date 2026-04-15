from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Iterable
from pathlib import Path
from queue import Queue
from foundation_kaia.logging.log_item import ILogItem
from .brainbox_report_item import BrainboxReportItem
import threading
from .brainbox_logger import ProgressItem, logger
from ...logging import Logger, HtmlReport

T = TypeVar('T')


class _QueueIterable(Generic[T]):
    def __init__(self):
        self._queue: Queue[BrainboxReportItem[T] | None] = Queue()
        self._error: Exception | None = None

    def _on_item(self, log_item: ILogItem):
        if isinstance(log_item, ProgressItem):
            self._queue.put(BrainboxReportItem(progress=log_item.progress))
        else:
            self._queue.put(BrainboxReportItem(log=log_item.to_string()))


    def end(self, error: Exception | None = None):
        self._error = error
        self._queue.put(None)

    def __enter__(self):
        Logger.ON_ITEM.append(self._on_item)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._on_item in Logger.ON_ITEM:
            Logger.ON_ITEM.remove(self._on_item)

    def __iter__(self):
        return self

    def __next__(self) -> BrainboxReportItem[T]:
        item = self._queue.get()
        if item is None:
            if self._error is not None:
                raise self._error
            raise StopIteration
        return item


class LongBrainboxProcess(ABC, Generic[T]):
    @abstractmethod
    def execute(self) -> T:
        pass

    def start_process(self, log_file_name: str|Path) -> Iterable[BrainboxReportItem[T]]:
        html_log_file = HtmlReport(Path(log_file_name))
        result_queue = _QueueIterable()

        def run():
            with html_log_file, result_queue:
                try:
                    result = self.execute()
                    result_queue._queue.put(BrainboxReportItem(result=result))
                    result_queue.end()
                except Exception as e:
                    logger.error(e)
                    result_queue.end(error=e)

        thread = threading.Thread(target=run)
        thread.start()

        return result_queue
