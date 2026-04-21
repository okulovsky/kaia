from chara.common import ICache, BrainBoxCache, Language, logger, BrainBoxPipeline
from pathlib import Path
from chara.common.tools.llm import PromptTaskBuilder
from ..utility_pipelines import CaseStatus
from .words_translation_case import WordTranslationCase


class WordTranslationCache(ICache[list[WordTranslationCase]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.llm = BrainBoxCache[WordTranslationCase, WordTranslationCase]()


class WordTranslationPipeline:
    def __init__(self, task_builder: PromptTaskBuilder,):
        self.task_builder = task_builder
        self.task_builder.read_default_prompt(Path(__file__).parent/'prompt.jinja')


    def _merge(self, case: WordTranslationCase, option: str):
        case.translation = option
        case.status = CaseStatus.success
        return case

    def __call__(self, cache: WordTranslationCache, cases: list[WordTranslationCase]):
        @logger.phase(cache.llm)
        def _():
            pipe = BrainBoxPipeline(self.task_builder, self._merge)
            pipe.run(cache.llm, cases)

        cache.write_result(list(cache.llm.read_options()))




