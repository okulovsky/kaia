import pandas as pd
from dataclasses import dataclass
from .log_item import ILogItem

@dataclass
class SeriesLogItem(ILogItem):
    s: pd.Series

    def _tostr(self):
        return str(self.s)

    def to_string(self) -> str:
        return self._tostr()

    def to_html(self) -> str:
        if len(self.s) == 0:
            return '[Empty series]'
        return self.s.to_frame().to_html()


@dataclass
class DataFrameLogItem(ILogItem):
    df: pd.DataFrame

    def _tostr(self):
        return str(self.df)

    def to_string(self) -> str:
        if self.df.shape[1] > 5:
            return f'[Dataframe of shape {self.df.shape}]'
        elif self.df.shape[0] > 10:
            return str(self.df.head(10))
        return self._tostr()

    def to_html(self) -> str:
        if self.df.shape[0] == 0:
            return '[Empty dataframe]'
        return self.df.to_html()