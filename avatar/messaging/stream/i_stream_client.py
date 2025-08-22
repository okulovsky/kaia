from typing import Iterable
from abc import ABC, abstractmethod
from .message import IMessage
import time
from ..amenities import ThreadCollection
from yo_fluq import Query, Queryable

class IStreamClient(ABC):
    @abstractmethod
    def put(self, message: IMessage):
        pass

    @abstractmethod
    def pull_all(self) -> Iterable[IMessage]:
        pass

    @abstractmethod
    def initialize(self):
        pass


    def _query(self, time_limit_in_seconds: float|None = None, no_exception: bool = False):
        begin = time.monotonic()
        collected_so_far = []
        while True:
            result = self.pull(1)
            collected_so_far.extend(result)
            yield from result
            if time_limit_in_seconds is not None and (time.monotonic() - begin) > time_limit_in_seconds:
                if no_exception:
                    return
                else:
                    if len(collected_so_far) == 0:
                        report = "NO MESSAGES RECEIVED"
                    else:
                        try:
                            report = ThreadCollection.just_print(collected_so_far, True)
                        except:
                            report = 'Errors when generating the report'
                    raise ValueError(f"Time limit exceed. Collected so far:\n\n{report}")
            time.sleep(0.01)

    def query(self, time_limit_in_seconds: float|None = None, no_exception: bool = False) -> Queryable[IMessage]:
        return Query.en(self._query(time_limit_in_seconds, no_exception))