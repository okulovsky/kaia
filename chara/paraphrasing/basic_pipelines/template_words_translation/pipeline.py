from chara.common import ICache, BrainBoxCache, Language, logger, BrainBoxPipeline
from pathlib import Path
from chara.common.tools.llm import PromptTaskBuilder
from ..utility_pipelines import UtilityCache, RepeatUntilDonePipeline, CaseStatus
from grammatron import Template
from .word_transformer import WordTransformer, WordTranslationCase


class WordTranslationCache(ICache[list[Template]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        t = BrainBoxCache[WordTranslationCase, WordTranslationCase]
        self.attempts = UtilityCache[WordTranslationCase,t](t)


class WordTranslationPipeline:
    def __init__(self, task_builder: PromptTaskBuilder, also_translate_option_headers: bool = False):
        self.task_builder = task_builder
        self.task_builder.set_default_jinja_prompter(Path(__file__).parent/'prompt.jinja')
        self.also_translate_option_headers = also_translate_option_headers


    def _merge(self, case: WordTranslationCase, option: str):
        case.translation = option
        case.status = CaseStatus.success
        return case

    def __call__(self, cache: WordTranslationCache, templates: list[Template]):
        transformer = WordTransformer(templates, self.also_translate_option_headers)
        cases = transformer.get_cases()


        @logger.phase(cache.attempts)
        def _():
            inner_pipeline = BrainBoxPipeline(self.task_builder, self._merge)
            pipe = RepeatUntilDonePipeline(inner_pipeline.run)
            pipe(cache.attempts, cases)

        result = cache.attempts.read_result()
        transformer.apply_cases(result)

        cache.write_result(transformer.templates)




