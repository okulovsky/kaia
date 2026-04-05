import os
from typing import Callable
from ..cache import ICacheEntity
from foundation_kaia.logging.logger_class import Logger as _Logger
from foundation_kaia.logging.simple import ExceptionItem
import pickle
import time



class Logger(_Logger):
    def phase(self,
              cache_entity: ICacheEntity,
              description: str|None = None,
              *,
              allow_unfilled_exit: bool = False):
        caption = cache_entity.name if description is None else description
        log_path = cache_entity.log_path

        def decorator(fn: Callable[[], None]):
            with self.section(caption):
                verb = 'failed'

                phase_log = []
                with self.with_callback(phase_log.append):

                    if not cache_entity.ready:
                        begin = time.monotonic()
                        try:
                            fn()
                            if not allow_unfilled_exit and not cache_entity.ready:
                                raise ValueError("Stage doesn't fill up the cache it was created for")
                            verb = 'completed'
                        except Exception as e:
                            self.log(ExceptionItem(e))
                            raise
                        finally:
                            end = time.monotonic()
                            try:
                                with open(log_path, 'wb') as stream:
                                    pickle.dump(phase_log, stream)
                            except Exception as e:
                                self.log("Can't save phase log to disk")
                            self.log(f"Stage {caption} {verb} in {int(end - begin)} seconds")
                    else:
                        self.log("Stage restored from cache")
                        if log_path.is_file():
                            with open(log_path, 'rb') as stream:
                                phase_log = pickle.load(stream)
                                for element in phase_log:
                                    self.log(element)

        return decorator
















