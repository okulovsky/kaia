from copy import deepcopy
from enum import Enum
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Callable
from .utility_cache import UtilityCache, TCache
from chara.common import logger

class CaseStatus(Enum):
    not_started = 0
    not_required = 1
    error = 2
    success = 3

T = TypeVar("T")

class RepeatUntilDonePipeline(Generic[T, TCache]):
    def __init__(self,
                 inner_pipeline: Callable[[TCache, list[T]], None],
                 status_field: str = 'status',
                 error_field: str|None = None,
                 history_field: str | None = None,
                 attempts: int = 5,
                 raise_if_unsuccessful: bool = True
                 ):
        self.inner_pipeline = inner_pipeline
        self.status_field = status_field
        self.error_field = error_field
        self.history_field = history_field
        self.attempts = attempts
        self.raise_if_unsuccessful = raise_if_unsuccessful


    def __call__(self, cache: UtilityCache[T, TCache], cases: list[T]):
        result = []

        @logger.phase(cache.buffer)
        def _():
            active_cases = []
            for case in cases:
                case = deepcopy(case)
                if self.history_field is not None:
                    if not hasattr(case, self.history_field):
                        setattr(case, self.history_field, [])
                    elif not isinstance(getattr(case, self.history_field), list):
                        setattr(case, self.history_field, [])
                active_cases.append(case)

            for i in range(self.attempts):
                if len(active_cases) == 0:
                    break

                subcache = cache.buffer.create_subcache(i)
                for case in active_cases:
                    setattr(case, self.status_field, CaseStatus.not_started)

                @logger.phase(subcache, f"Attempt #{i}")
                def __():
                    self.inner_pipeline(subcache, active_cases)

                attempt_result: list[T] = list(subcache.read_result())
                if len(attempt_result) != len(active_cases):
                    raise ValueError(f"Pipeline must process all the cases provided, and return all of them. Cases submitted {len(active_cases)}, cases received {len(attempt_result)}")
                active_cases = []
                for case in attempt_result:
                    status = getattr(case, self.status_field)
                    error = None
                    if self.error_field is not None:
                        error = getattr(case, self.error_field)
                        setattr(case, self.error_field, None)
                    if self.history_field is not None:
                        getattr(case, self.history_field).append((status, error))

                    if status == CaseStatus.not_started:
                        raise ValueError(f"Pipeline should set field {self.status_field} of the case to something, not keep a default 'not_started'")
                    elif status == CaseStatus.error:
                        active_cases.append(case)
                    else:
                        result.append(case)

            if len(active_cases) != 0 and self.raise_if_unsuccessful:
                raise ValueError(f"After {self.attempts} attempts, there were still {len(active_cases)} unsuccesful cases")
            result.extend(active_cases)
            cache.buffer.finalize()



        cache.write_result(result)




