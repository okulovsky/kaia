from pathlib import Path
from chara.common import ICache, BrainBoxCache, logger, BrainBoxUnit
from chara.paraphrasing.common.llm_tools import PromptTaskBuilder, BulletPointDivider
from .negative_case import NegativeCase


class NegativePipelineCache(ICache[list[str]]):
    def __init__(self, working_directory: Path | None = None):
        super().__init__(working_directory)
        self.llm = BrainBoxCache[NegativeCase, str]()


class NegativePipeline:
    def __init__(self, builder: PromptTaskBuilder):
        self.builder = builder

    def __call__(self, cache: NegativePipelineCache, cases: list[NegativeCase],
                 output_path: Path | None = None):
        @logger.phase(cache.llm, "Running LLM")
        def _():
            unit = BrainBoxUnit(self.builder, None, BulletPointDivider())
            unit.run(cache.llm, cases)

        seen = set()
        result = []
        for _, phrase in cache.llm.read_cases_and_options():
            text = phrase.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)

        cache.write_result(result)

        if output_path is not None:
            output_path.write_text('\n'.join(result), encoding='utf-8')
            logger.log(f"{len(result)} negative phrases → {output_path}")
