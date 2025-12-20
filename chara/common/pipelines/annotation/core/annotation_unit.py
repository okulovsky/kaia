import time
from foundation_kaia.fork import Fork
from .annotator import IAnnotator, TCache
from typing import Generic
from functools import partial

class AnnotationUnit(Generic[TCache]):
    TEST_MODE: bool = False

    def __init__(self, annotator: IAnnotator[TCache]):
        self.annotator = annotator

    def start(self, cache: TCache):
        if cache.ready:
            return None

        if AnnotationUnit.TEST_MODE:
            self.annotator.mock_annotation(cache)
            return None


        fork = Fork(partial(self.annotator.run, cache))
        fork.start()
        return fork

    def end(self, fork, cache: TCache):
        if fork is None:
            return
        try:
            while True:
                if cache.ready:
                    break
                time.sleep(1)
        finally:
            fork.terminate()

    def run(self, cache: TCache):
        fork = self.start(cache)
        self.end(fork, cache)
