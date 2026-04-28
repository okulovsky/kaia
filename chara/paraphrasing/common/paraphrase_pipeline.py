from dataclasses import dataclass
from chara.common import *
from chara.common.tools.llm import PromptTaskBuilder
from .template_paraphrasing import  (
    TemplateParaphrasePipeline, TemplateParaphraseCase,
    TemplateParaphraseCaseManager
)
from .words_translation import WordTranslationCaseManager, WordTranslationPipeline, WordTranslationCase
from .grammar_correction import GrammarCorrectionPipeline, GrammarCorrectionCase, GrammarCorrectionCaseManager
from .options_expanding import OptionExpandingCase, OptionExpandingCaseManager, OptionExpandingPipeline
from pathlib import Path

@dataclass
class ParaphrasePipelineSettings:
    paraphrase_task_builder: PromptTaskBuilder[TemplateParaphraseCase]
    enable_words_translation: bool = True
    grammar_correction_attempts: int|None = 1
    words_translation_attempts: int|None = 1
    enable_options_expanding: bool = False


class ParaphraseCache(CaseCache[TemplateParaphraseCase]):
    def __init__(self, working_folder: Path | None = None):
        super().__init__(working_folder)
        self.parsed_template_paraphrasing = CaseCache[TemplateParaphraseCase]()
        self.words_translation = CaseCache[WordTranslationCase]()
        self.grammar_correction = CaseCache[GrammarCorrectionCase]()
        self.options_expanding = CaseCache[OptionExpandingCase]()


class ParaphrasePipeline:
    def __init__(self, settings: ParaphrasePipelineSettings):
        self.settings = settings

    def __call__(self, cache: ParaphraseCache, cases: list[TemplateParaphraseCase]):

        parsed_template_manager = TemplateParaphraseCaseManager(cases)
        cases = parsed_template_manager.prepare()
        @logger.phase(cache.parsed_template_paraphrasing)
        def _():
            pipe = TemplateParaphrasePipeline(self.settings.paraphrase_task_builder)
            pipe(cache.parsed_template_paraphrasing, cases=cases)
        templates = parsed_template_manager.apply(cache.parsed_template_paraphrasing.read_cases())

        if self.settings.enable_words_translation:
            manager = WordTranslationCaseManager(templates, True)
            translation_cases = manager.prepare()
            @logger.phase(cache.words_translation)
            def _():
                task_builder = PromptTaskBuilder(self.settings.paraphrase_task_builder.model)
                pipe = WordTranslationPipeline(task_builder)
                pipe(cache.words_translation, translation_cases)
            templates = manager.apply(cache.words_translation.read_result())
        else:
            cache.words_translation.finalize()

        if self.settings.grammar_correction_attempts is not None:
            manager = GrammarCorrectionCaseManager(templates)
            grammar_cases = manager.prepare()
            @logger.phase(cache.grammar_correction)
            def _():
                task_builder = PromptTaskBuilder(self.settings.paraphrase_task_builder.model)
                pipe = GrammarCorrectionPipeline(task_builder)
                if self.settings.grammar_correction_attempts > 1:
                    pipe = ChooseBestAnswerPipeline(pipe, self.settings.grammar_correction_attempts)
                pipe(cache.grammar_correction, grammar_cases)
            templates = manager.apply(cache.grammar_correction.read_result())
        else:
            cache.grammar_correction.finalize()

        if self.settings.enable_options_expanding:
            manager = OptionExpandingCaseManager(templates)
            options_cases = manager.prepare()
            @logger.phase(cache.options_expanding)
            def _():
                task_builder = PromptTaskBuilder(self.settings.paraphrase_task_builder.model)
                pipe = OptionExpandingPipeline(task_builder)
                pipe(cache.options_expanding, options_cases)
            templates = manager.apply(cache.options_expanding.read_result())
        else:
            cache.options_expanding.finalize()

        result = []
        for template in templates:
            case: TemplateParaphraseCase = template._stored_info
            case.resulting_template = template
            del template._stored_info
            result.append(case)
        cache.write_result(result)











