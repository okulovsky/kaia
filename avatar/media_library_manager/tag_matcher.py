from typing import *
from abc import ABC, abstractmethod

class ITagMatcher(ABC):
    @abstractmethod
    def match(self, tags: dict[str, str], additional_required_tags: None|dict[str,str]) -> bool:
        pass

class ITagMatcherFactory(ABC):
    @abstractmethod
    def prepare(self, state: dict[str, str]) -> ITagMatcher:
        pass


class ExactTagMatcher(ITagMatcher):
    def __init__(self, expected_tags: dict[str, str]):
        self.expected_tags = expected_tags

    def _yeild_key_values(self, additional_required_tags: None|dict[str,str]):
        yield from self.expected_tags.items()
        if additional_required_tags is not None:
            yield from additional_required_tags.items()

    def match(self, tag: dict[str, str], additional_required_tags: None|dict[str,str]) -> bool:
        for key, value in self._yeild_key_values(additional_required_tags):
            if not key in tag:
                return False
            if tag[key] != value:
                return False
        return True

    class Factory1to1(ITagMatcherFactory):
        def prepare(self, state: dict[str, str]) -> ITagMatcher:
            return ExactTagMatcher({k:v for k,v in state.items()})

    class CustomFactory(ITagMatcherFactory):
        def __init__(self, custom_state_transformer):
            self.custom_state_transformer = custom_state_transformer

        def prepare(self, state: dict[str, str]) -> ITagMatcher:
            tags = self.custom_state_transformer(state)
            return ExactTagMatcher(tags)

    class SubsetFactory(ITagMatcherFactory):
        def __init__(self, *fields_to_take: str):
            self.fields_to_take = fields_to_take

        def prepare(self, state: dict[str, str]) -> ITagMatcher:
            tags = {k: state[k] for k in self.fields_to_take}
            return ExactTagMatcher(tags)



