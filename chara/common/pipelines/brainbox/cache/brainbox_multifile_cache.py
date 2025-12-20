from .....common import MultifileCache
from .brainbox_cache_item import BrainBoxUnitResultItem, TCase, TOption
from typing import Generic

class BrainBoxMultifileCache(Generic[TCase, TOption], MultifileCache[BrainBoxUnitResultItem[TCase, TOption]]):
    def _write_and_update_counts(self, item: BrainBoxUnitResultItem[TCase, TOption], counts):
        super()._write_and_update_counts(item, counts)
        if item.options is not None:
            counts['options']+=len([z for z in item.options if z.option is not None])

    def _initialize_counts(self):
        return dict(records=0, options=0)