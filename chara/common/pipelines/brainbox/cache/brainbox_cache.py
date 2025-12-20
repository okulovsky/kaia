from .....common import *
from brainbox import BrainBox
from typing import TypeVar, Generic
from yo_fluq import Queryable, FileIO
from .brainbox_cache_item import BrainBoxUnitResultItem
from .brainbox_multifile_cache import BrainBoxMultifileCache

TCase = TypeVar("TCase")
TOption = TypeVar("TOption")


class BrainBoxCache(Generic[TCase, TOption], ICache[None]):
    def __init__(self):
        super().__init__()
        self.tasks = FileCache[list[BrainBox.ITask]]()
        self.task_id = FileCache[str](FileCache.Type.Text)
        self.result = BrainBoxMultifileCache[TCase, TOption]()
        self.files = FolderCache()


    def _read_cases_and_options(self):
        for case in self.result.read():
            if case.options is not None:
                for option in case.options:
                    if option.option is not None:
                        yield case.case, option.option


    def read_options(self) -> Queryable[TOption]:
        counts = FileIO.read_json(self.result.counts_file)
        return Queryable(self._read_cases_and_options(), counts['options']).select(lambda z: z[1])

    def read_cases_and_options(self) -> Queryable[tuple[TCase, TOption]]:
        counts = FileIO.read_json(self.result.counts_file)
        return Queryable(self._read_cases_and_options(), counts['options'])

    def _item_to_case_and_single_option(self, item: BrainBoxUnitResultItem[TCase, TOption]) -> tuple[TCase, TOption]|None:
        if item.options is None:
            return None
        if len(item.options) > 1:
            raise ValueError("Expected no more than one option for each case")
        if item.options[0].option is not None:
            return item.case, item.options[0].option
        return None

    def read_cases_and_single_options(self):
        return (
            self.read_result()
            .select(self._item_to_case_and_single_option)
            .where(lambda z: z is not None)
        )

    def read_result(self) -> Queryable[BrainBoxUnitResultItem[TCase, TOption]]:
        return self.result.read()

    def get_file_path(self, option: str):
        return self.files.working_folder/option

    def open_file(self, option: str):
        return self.files.read_file(option)





