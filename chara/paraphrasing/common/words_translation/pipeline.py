from chara.common import logger, BrainBoxCasePipeline, CaseCache
from pathlib import Path
from chara.common.tools.llm import PromptTaskBuilder
from .words_translation_case import WordTranslationCase


class WordTranslationPipeline:
    def __init__(self, task_builder: PromptTaskBuilder,):
        self.task_builder = task_builder
        self.task_builder.read_default_prompt(Path(__file__).parent/'prompt.jinja')

    def _merge(self, case: WordTranslationCase, option: str):
        case.translation = option

    def __call__(self, cache: CaseCache[WordTranslationCase], cases: list[WordTranslationCase]):
        subcache = cache.create_subcache('llm')
        @logger.phase(subcache)
        def _():
            pipe = BrainBoxCasePipeline(self.task_builder, self._merge)
            pipe(subcache, cases)

        cache.write_result(subcache.read_cases())




