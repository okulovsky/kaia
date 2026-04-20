from copy import deepcopy
from enum import Enum
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Callable
from .utility_cache import UtilityCache, TCache
from chara.common import logger

class IVotingCase(ABC):
    @abstractmethod
    def get_result_fingerprint(self) -> str:
        pass

T = TypeVar('T', bound=IVotingCase)

class ChooseBestAnswerPipeline(Generic[T, TCache]):
    def __init__(self,
                 inner_pipeline: Callable[[TCache, list[T]], None],
                 vote_group_field: str = 'vote_group',
                 poll_size: int = 3
                 ):
        self.inner_pipeline = inner_pipeline
        self.vote_group_field = vote_group_field
        self.poll_size = poll_size

    def __call__(self, cache: UtilityCache[T, TCache], cases: list[T]) -> None:

        @logger.phase(cache.buffer)
        def _():
            for i in range(self.poll_size):
                subcache = cache.buffer.create_subcache(i)

                active_cases = []
                for index, case in enumerate(cases):
                    case = deepcopy(case)
                    setattr(case, self.vote_group_field, index)
                    active_cases.append(case)

                @logger.phase(subcache)
                def __():
                    self.inner_pipeline(subcache, active_cases)
            cache.buffer.finalize()

        result = {}
        for subcache in cache.buffer.read_subcaches():
            round_cases: list[T] = subcache.read_result()
            for case in round_cases:
                id = getattr(case, self.vote_group_field)
                if id not in result:
                    result[id] = {}
                fingerprint = case.get_result_fingerprint()
                if fingerprint not in result[id]:
                    result[id][fingerprint] = []
                result[id][fingerprint].append(case)

        final_result = []
        for id in sorted(result.keys()):
            best_fingerprint = min(result[id], key=lambda fp: (-len(result[id][fp]), fp))
            final_result.append(result[id][best_fingerprint][0])

        cache.write_result(final_result)




