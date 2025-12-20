from brainbox import BrainBox
from .cache import TCase, TOption
from typing import Any, Callable, Generic
from abc import ABC, abstractmethod

class IBrainBoxMerger(Generic[TCase, TOption], ABC):
    @abstractmethod
    def divide(self, api: BrainBox.Api, result: Any) -> list:
        pass

    @abstractmethod
    def merge(self, api: BrainBox.Api, case: TCase, option: Any) -> TOption:
        pass


class BrainBoxMerger(Generic[TCase, TOption], IBrainBoxMerger[TCase, TOption]):
    def __init__(self,

                 ):
        self.merger = merger
        self.divider = divider

    def divide(self, api: BrainBox.Api, result: Any) -> list:
        if self.divider is None:
            return [result]
        return self.divider(result)

    def merge(self, api: BrainBox.Api, case: TCase, option: Any) -> TOption:
        if self.merger is None:
            return option
        return self.merger(case, option)



