from typing import Callable

from .image_scenario import IImageScenario
from ..activity import ImageRequest
from chara import ICasePipeline, CaseCollection, logger, Chara
from typing import Generic, TypeVar

TImageScenario = TypeVar("TImageScenario", bound=IImageScenario)

class ScenarioPipeline(Generic[TImageScenario]):
    def __init__(self,
                 case_factory: Callable[[ImageRequest], IImageScenario],
                 steps: list[tuple[str,ICasePipeline[TImageScenario]]]):
        self.case_factory = case_factory
        self.steps = steps

    def __call__(self, request: list[ImageRequest]) -> CaseCollection[TImageScenario]:
        cases = CaseCollection(self.case_factory(r) for r in request)
        for name, step in self.steps:
            logger.info(f"Running {name}")
            cases = Chara.call(step)(cases)
            cases = cases.raise_if_all_errors().successes_collection
        return cases