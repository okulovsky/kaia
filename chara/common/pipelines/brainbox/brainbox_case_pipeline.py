from copy import deepcopy
from typing import Callable, Generic, Any
from ..cases import TCase, CaseCollection, ICasePipeline
from brainbox import BrainBox
from .brainbox_pipeline import ResultToFiles, brainbox_pipeline
from ...architecture import Chara
import traceback
from .brainbox_case_pipeline_uploader import BrainBoxCasePipelineUploader

class BrainBoxCasePipeline(Generic[TCase], ICasePipeline[TCase]):
    Uploader = BrainBoxCasePipelineUploader

    def __init__(self,
                 task_builder: Callable[[TCase], BrainBox.Task],
                 applicator: Callable[[TCase, Any], None]|str|None,
                 divider: Callable[[Any], list[Any]]|None = None,
                 result_to_file: ResultToFiles = None,
                 uploader: BrainBoxCasePipelineUploader[TCase]|None = None,
                 remove_resulting_files_from_cache: bool = False,
                 ):
        self.task_builder = task_builder
        self.applicator = applicator
        self.divider = divider
        self.result_to_file = result_to_file
        self.remove_resulting_files_from_cache = remove_resulting_files_from_cache
        self.uploader = uploader

    def _apply(self, case: TCase, result: Any):
        if self.applicator is None:
            return
        if isinstance(self.applicator, str):
            setattr(case, self.applicator, result)
        else:
            try:
                self.applicator(case, result)
            except Exception:
                case.error = "Application error: \n"+traceback.format_exc()

    def __call__(self, cases: CaseCollection[TCase]) -> CaseCollection[TCase]:
        active_cases = cases.clone().successes
        tasks = [self.task_builder(case) for case in active_cases]

        names = None
        if self.uploader is not None:
            names = Chara.call(self.uploader.upload)(active_cases)

        results = Chara.call(brainbox_pipeline)(tasks, self.result_to_file, self.remove_resulting_files_from_cache)

        output_cases = []
        for case, result in zip(active_cases, results.read_all()):
            if result.error is not None:
                case.error = result.error
                output_cases.append(case)
                continue
            if self.divider is None:
                self._apply(case, result.result)
                output_cases.append(case)
                continue
            else:
                try:
                    subresults = self.divider(result.result)
                except Exception:
                    case.error = "Division error: \n"+traceback.format_exc()
                    output_cases.append(case)
                    continue
                for subresult in subresults:
                    new_case = deepcopy(case)
                    self._apply(new_case, subresult)
                    output_cases.append(new_case)

        if self.uploader is not None:
            Chara.call(self.uploader.cleanup)(names)

        return CaseCollection(output_cases, cases.errors)









