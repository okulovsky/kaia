from pathlib import Path
from chara.common import ICache, BrainBoxCache, logger, BrainBoxUnit
from chara.paraphrasing.common.llm_tools import PromptTaskBuilder, BulletPointDivider
from .intent_case import IntentCase


class IntentPipelineCache(ICache[list]):
    def __init__(self, working_directory: Path | None = None):
        super().__init__(working_directory)
        self.llm = BrainBoxCache[IntentCase, str]()


class IntentPipeline:
    def __init__(self, builder: PromptTaskBuilder):
        self.builder = builder

    def __call__(self, cache: IntentPipelineCache, cases: list[IntentCase]):
        @logger.phase(cache.llm, "Running LLM")
        def _():
            unit = BrainBoxUnit(self.builder, None, BulletPointDivider())
            unit.run(cache.llm, cases)

        result = list(cache.llm.read_cases_and_options())
        cache.write_result(result)
