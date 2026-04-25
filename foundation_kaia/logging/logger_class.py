from typing import Callable, Any, TypeVar
from .simple import HeaderItem, ILogItem
from contextlib import contextmanager
from datetime import datetime

T = TypeVar('T')


class _UndeclaredClass:
    pass


class Section:
    def __init__(self, logger: 'Logger', caption: str):
        self._logger = logger
        self._caption = caption

    def __enter__(self):
        self._logger.log(HeaderItem(self._logger.current_level, self._caption))
        self._logger.current_level += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logger.current_level -= 1


class Logger:
    ON_ITEM: list[Callable[[ILogItem], None]] = []

    def __init__(self):
        self.current_level = 0

    def reset(self):
        self.items = []
        self.current_level = 0

    def section(self, caption: str) -> Section:
        return Section(self, caption)

    def log(self, message: Any):
        if not isinstance(message, ILogItem):
            message = self.resolve(message)
        message.timestamp = datetime.now()
        for callback in Logger.ON_ITEM:
            callback(message)

    def info(self, message: Any)->None:
        self.log(message)

    def error(self, message: Exception):
        self.log(message)

    @contextmanager
    def with_callback(self, callable: Callable[[ILogItem], None]):
        Logger.ON_ITEM.append(callable)
        yield
        Logger.ON_ITEM.remove(callable)

    def resolve(self, o: Any) -> Any:
        from .simple import LineItem, ObjectItem, ExceptionItem
        from .pandas_log import SeriesLogItem, DataFrameLogItem
        from .matplotlib_log import FigureLogItem
        from .ipywidgets_log import WidgetLogItem
        if isinstance(o, str):
            return LineItem(o)
        if isinstance(o, BaseException):
            return ExceptionItem(o)

        try:
            from pandas import Series, DataFrame
        except Exception:
            Series = _UndeclaredClass
            DataFrame = _UndeclaredClass

        if isinstance(o, Series):
            return SeriesLogItem(o)
        if isinstance(o, DataFrame):
            return DataFrameLogItem(o)

        try:
            from matplotlib.axes import Axes
            from matplotlib.figure import Figure
        except Exception:
            Axes = _UndeclaredClass
            Figure = _UndeclaredClass

        if isinstance(o, Axes):
            return FigureLogItem(o.figure)
        if isinstance(o, Figure):
            return FigureLogItem(o)

        try:
            from ipywidgets import Widget
        except Exception:
            Widget = _UndeclaredClass

        if isinstance(o, Widget):
            return WidgetLogItem(o)

        return ObjectItem(o)

















