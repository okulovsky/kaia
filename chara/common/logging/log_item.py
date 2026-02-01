from abc import ABC, abstractmethod
from typing import Any
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from ipywidgets import Widget



class ILogItem(ABC):
    @abstractmethod
    def to_string(self) -> str:
        pass

    def to_html(self) -> str:
        pass

    def validate(self, parameter: float):
        pass

    @staticmethod
    def create(o: Any) -> 'ILogItem':
        from .simple import LineItem, ObjectItem, ExceptionItem
        from .pandas_log import SeriesLogItem, DataFrameLogItem
        from .matplotlib_log import FigureLogItem
        from .ipywidgets_log import WidgetLogItem
        if isinstance(o, str):
            return LineItem(o)
        if isinstance(o, BaseException):
            return ExceptionItem(o)
        if isinstance(o, pd.Series):
            return SeriesLogItem(o)
        if isinstance(o, pd.DataFrame):
            return DataFrameLogItem(o)
        if isinstance(o, Axes):
            return FigureLogItem(o.figure)
        if isinstance(o, Figure):
            return FigureLogItem(o)
        if isinstance(o, Widget):
            return WidgetLogItem(o)

        return ObjectItem(o)

