from dataclasses import dataclass
from chara.common import Chara, ChooseBestAnswerPipeline, CaseCollection
from chara.common.tools.llm import PromptTaskBuilder
from .template_paraphrasing import TemplateParaphrase, ParaphraseCase
from .words_translation import WordTranslation
from .grammar_correction import GrammarCorrection
from .options_expanding import OptionExpanding


@dataclass
class ParaphrasePipelineSettings:
    paraphrase_task_builder: PromptTaskBuilder[ParaphraseCase]
    enable_words_translation: bool = True
    grammar_correction_attempts: int | None = 1
    words_translation_attempts: int | None = 1
    enable_options_expanding: bool = False
    enable_option_values_translation: bool = False


class ParaphrasePipeline:
    def __init__(self, settings: ParaphrasePipelineSettings):
        self.settings = settings

    def __call__(self, cases: CaseCollection[ParaphraseCase]) -> CaseCollection[ParaphraseCase]:
        from .paraphrase import Paraphrase

        paraphrase_manager = Paraphrase(cases.successes)
        expanded_cases = paraphrase_manager.prepare()

        paraphrase_pipe = TemplateParaphrase.Pipeline(self.settings.paraphrase_task_builder)
        paraphrase_results = Chara.call(paraphrase_pipe)(expanded_cases)
        templates = paraphrase_manager.apply(paraphrase_results.successes)

        if self.settings.enable_words_translation:
            translation_manager = WordTranslation(templates, self.settings.enable_option_values_translation)
            translation_cases = translation_manager.prepare()
            if translation_cases:
                translation_pipe = WordTranslation.Pipeline(
                    PromptTaskBuilder(self.settings.paraphrase_task_builder.model)
                )
                translation_result = Chara.call(translation_pipe)(translation_cases)
                templates = translation_manager.apply(translation_result.successes)

        if self.settings.grammar_correction_attempts is not None:
            grammar_manager = GrammarCorrection(templates)
            grammar_cases = grammar_manager.prepare()
            if grammar_cases:
                grammar_pipe = GrammarCorrection.Pipeline(
                    PromptTaskBuilder(self.settings.paraphrase_task_builder.model)
                )
                if self.settings.grammar_correction_attempts > 1:
                    grammar_pipe = ChooseBestAnswerPipeline(grammar_pipe, self.settings.grammar_correction_attempts)
                grammar_result = Chara.call(grammar_pipe)(grammar_cases)
                templates = grammar_manager.apply(grammar_result.successes)

        if self.settings.enable_options_expanding:
            options_manager = OptionExpanding(templates)
            options_cases = options_manager.prepare()
            if options_cases:
                options_pipe = OptionExpanding.Pipeline(
                    PromptTaskBuilder(self.settings.paraphrase_task_builder.model)
                )
                options_results = Chara.call(options_pipe)(options_cases)
                templates = options_manager.apply(options_results.successes)

        result = []
        for template in templates:
            case: ParaphraseCase = template._case
            case.resulting_template = template
            del template._case
            result.append(case)

        return CaseCollection(result)
