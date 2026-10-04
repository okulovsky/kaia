from collections import OrderedDict
from typing import Any, Iterable
from .record import IRecord
from .feedback import Feedback
from .strategies import IContentStrategy, NewContentStrategy
from .tag_matcher import ITagMatcher, TagMatcher


class ContentFinder:
    def __init__(self, strategy: IContentStrategy|None = None):
        self.strategy = strategy if strategy is not None else NewContentStrategy(randomize=False)
        self.debug = False

    def _filter(self, records: Iterable[IRecord], matchers: list[ITagMatcher]) -> list[IRecord]:
        result = []
        for index, record in enumerate(records):
            tags = record.get_tags()
            skip = False
            for matcher in matchers:
                comparison = matcher.match(tags)
                if comparison is not None:
                    skip = True
                    if self.debug:
                        print(f'TAG MATCHER: At #{index} {comparison}  {record}')
                    break
            if not skip:
                result.append(record)
        return result

    def select(self,
               records: Iterable[IRecord],
               strong: dict[str, Any]|None = None,
               weak: dict[str, Any]|None = None,
               fuzzy: 'OrderedDict[str, Any]|None' = None,
               ) -> list[IRecord]:
        records = list(records)
        matchers = []
        if strong is not None:
            matchers.append(TagMatcher(True, strong))
        if weak is not None:
            matchers.append(TagMatcher(False, weak))

        if not fuzzy:
            return self._filter(records, matchers)

        keys = list(fuzzy.keys())
        for cutoff in range(len(keys), -1, -1):
            fuzzy_matchers = list(matchers)
            if cutoff > 0:
                subset = {key: fuzzy[key] for key in keys[:cutoff]}
                fuzzy_matchers.append(TagMatcher(False, subset))
            filtered = self._filter(records, fuzzy_matchers)
            if len(filtered) > 0:
                return filtered
        return []

    def choose(self, records: Iterable[IRecord], feedback: Feedback) -> IRecord|None:
        return self.strategy.choose(list(records), feedback)

    def find(self,
             records: Iterable[IRecord],
             feedback: Feedback,
             strong: dict[str, Any]|None = None,
             weak: dict[str, Any]|None = None,
             fuzzy: 'OrderedDict[str, Any]|None' = None,
             ) -> IRecord|None:
        return self.choose(self.select(records, strong, weak, fuzzy), feedback)
