from ...common.tools.llm import PromptTaskBuilder
from ...paraphrasing.basic_pipelines import *
from chara.common import *
from pathlib import Path
from grammatron import Template
from dataclasses import dataclass

@dataclass
class DatasetGenerationInfo:
    mood: str
    original_template_name: str

class DatasetGenerationCache(ICache[list[Template]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.template_paraphrasing = TemplateParaphraseCache()
        self.words_translation = WordTranslationCache() #maybe add attempts
        self.grammar_correction = GrammarCorrectionCache() #maybe add voting
        self.options_expanding = OptionExpandingCache() #maybe add attempts


class DatasetGenerationPipeline:
    def __init__(self,
                 llm_model: str,
                 moods: list[str],
                 target_languages: list[str]
                 ):
        self.llm_model = llm_model
        self.moods = moods
        self.target_languages = target_languages


    def __call__(self, cache: DatasetGenerationCache, templates: list[Template]):
        template_paraphrasing_cases = []
        for mood in self.moods:
            for language in self.target_languages:
                for template in templates:
                    for parsed_template in ParsedTemplate.parse(template):
                        case = TemplateParaphraseCase(
                            DatasetGenerationInfo(
                                mood = mood,
                                original_template_name=template.get_name()
                            ),
                            parsed_template,
                            language
                        )
                        template_paraphrasing_cases.append(case)

        @logger.phase(cache.template_paraphrasing)
        def _():
            task_builder = PromptTaskBuilder(
                self.llm_model,
                prompt_file=Path(__file__).parent/'template_prompt.jinja',
                debug = True
            )
            pipe = TemplateParaphrasePipeline(task_builder)
            pipe(cache.template_paraphrasing, template_paraphrasing_cases)

        templates = []
        for case in cache.template_paraphrasing.read_result():
            template = case.template
            template._stored_info = case.info
            templates.append(template)

        manager = WordTranslationCaseManager(templates, True)
        translation_cases = manager.prepare()
        @logger.phase(cache.words_translation)
        def _():
            task_builder = PromptTaskBuilder(self.llm_model)
            pipe = WordTranslationPipeline(task_builder)
            pipe(cache.words_translation, translation_cases)

        templates = manager.apply(cache.words_translation.read_result())

        manager = GrammarCorrectionCaseManager(templates)
        grammar_cases = manager.prepare()
        @logger.phase(cache.grammar_correction)
        def _():
            task_builder = PromptTaskBuilder(self.llm_model)
            pipe = GrammarCorrectionPipeline(task_builder)
            pipe(cache.grammar_correction, grammar_cases)
        templates = manager.apply(cache.grammar_correction.read_result())

        manager = OptionExpandingCaseManager(templates)
        options_cases = manager.prepare()
        @logger.phase(cache.options_expanding)
        def _():
            task_builder = PromptTaskBuilder(self.llm_model)
            pipe = OptionExpandingPipeline(task_builder)
            pipe(cache.options_expanding, options_cases)
        templates = manager.apply(cache.options_expanding.read_result())

        cache.write_result(templates)







