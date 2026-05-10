import time
from foundation_kaia.fork import Fork
from .annotator import IAnnotator, TCase
from typing import Generic, Callable
from functools import partial
from ....architecture import Chara
from ...cases import CaseCollection

class AnnotationPipeline(Generic[TCase]):
    TEST_MODE: bool = False

    def __init__(self, annotator: IAnnotator, annotation_field: str|Callable[[TCase, None], None]):
        self.annotator = annotator
        self.annotation_field = annotation_field

    def start(self, cases: tuple[TCase,...]):
        fork = Fork(partial(self.annotator.run, cases=cases, folder=Chara.current.folder))
        fork.start()
        return fork

    def end(self, fork):
        if fork is None:
            return
        try:
            path = Chara.current.folder/'.finished'
            while True:
                if path.is_file():
                    path.unlink()
                    break
                if fork.process.poll() is not None:
                    raise RuntimeError(
                        f"Annotator process exited with code {fork.process.returncode} before finishing"
                    )
                time.sleep(1)
        finally:
            fork.terminate()

    def __call__(self, cases: CaseCollection[TCase]) -> CaseCollection[TCase]:
        active_cases = cases.clone().successes
        fork = self.start(active_cases)
        self.end(fork)
        result = self.annotator.get_result(Chara.current.folder)
        for case in active_cases:
            id = case.get_id()
            if id in result:
                if isinstance(self.annotation_field, str):
                    setattr(case, self.annotation_field, result[id])
                else:
                    self.annotation_field(case, result)
            else:
                case.error = "Was not annotated"
        return CaseCollection(cases.errors, active_cases)
