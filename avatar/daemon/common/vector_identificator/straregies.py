import pandas as pd
from abc import ABC, abstractmethod

class IStrategy(ABC):
    @abstractmethod
    def get_winner(self, s: pd.Series):
        pass


class BestOfStrategy(IStrategy):
    def __init__(self, k: int = 10):
        self.k = k

    def get_winner(self, s: pd.Series):
        df = s.sort_values().to_frame('distance').reset_index()
        df = df.iloc[:self.k]
        return (
            df
            .groupby('index')
            .size()
            .sort_values(ascending=False)
            .index[0]
        )