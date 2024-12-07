from typing import *
import pandas as pd
import numpy as np
from enum import Enum
import re

class Ontology:
    @staticmethod
    def start(count=1, id_column: str|None = None):
        df = pd.DataFrame([{}]*count)
        if id_column is not None:
            df[id_column] = list(range(df.shape[0]))
        return df

    @staticmethod
    def _clear_nones(df):
        for c in df.columns:
            df[c] = np.where(df[c].isnull(), None, df[c])
        return df


    @staticmethod
    def product(df: pd.DataFrame, *dfs: pd.DataFrame):
        current = df
        for mdf in dfs:
            current = (
                current
                .assign(_=1)
                .merge(
                    mdf.assign(_=1),
                    left_on='_',
                    right_on='_'
                )
                .drop('_', axis=1)
            )
        current = current.reset_index(drop=True)
        return current

    @staticmethod
    def concat(df: pd.DataFrame, *dfs: pd.DataFrame):
        current = pd.concat([df]+list(dfs))
        current = current.reset_index(drop=True)
        return Ontology._clear_nones(current)

    @staticmethod
    def options(column_name, *options):
        return pd.DataFrame({column_name:list(options)})

    @staticmethod
    def enum_options(column_name, enum: Type[Enum], without: Iterable = ()):
        return Ontology.options(column_name, *[e for e in enum if e not in without])

    @staticmethod
    def prettify_prompt(s):
        return re.sub('(\n+)','\n\n',s.strip())