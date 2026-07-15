from chara import Chara, logger
from chara.common import ICasePipeline, CaseCollection
from .case import ImageScenarioCase


class ImageScenarioPipeline:
    def __init__(self, steps: list[tuple[str,ICasePipeline[ImageScenarioCase]]]):
        self.steps = steps

    def __call__(self, cases: CaseCollection[ImageScenarioCase]) -> CaseCollection[ImageScenarioCase]:
        for name, step in self.steps:
            logger.info(f"Running {name}")
            cases = Chara.call(step)(cases)
            cases = cases.raise_if_all_errors().successes_collection
        return cases