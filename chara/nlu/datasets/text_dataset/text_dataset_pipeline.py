from chara.paraphrasing.common import Paraphrase, ParsedTemplate, generate_values_for_variables
from pathlib import Path
from grammatron import Template
from chara.common import Chara
from chara.common.tools.llm import PromptTaskBuilder


class TextDatasetCase(Paraphrase.Case):
    def __init__(self, template: Template, language: str, mood: str):
        super().__init__(template, language)
        self.mood = mood


class TextDatasetPipeline:
    def __init__(self, model: str, templates: list[Template], languages: list[str], moods: list[str]):
        self.model = model
        self.templates = templates
        self.languages = languages
        self.moods = moods

    def __call__(self) -> list[dict]:
        cases = []
        for mood in self.moods:
            for language in self.languages:
                for template in self.templates:
                    cases.append(TextDatasetCase(template, language, mood))
        builder = PromptTaskBuilder(self.model, Path(__file__).parent / "template_prompt.jinja")
        settings = Paraphrase.Settings(
            paraphrase_task_builder=builder,
            enable_words_translation=True,
            grammar_correction_attempts=3,
            words_translation_attempts=3,
            enable_options_expanding=True,
            enable_option_values_translation=True,
        )
        pipe = Paraphrase.Pipeline(settings)
        paraphrase_results = Chara.call(pipe)(cases)
        return self._export_cases(paraphrase_results)

    def _export_cases(self, cases):
        result = []
        for case in cases:
            intent = case.original_template.get_name()
            variables = ParsedTemplate.parse_single(case.resulting_template).variables
            if len(variables) == 0:
                values_instances = [{}]
            else:
                values_instances = generate_values_for_variables(list(variables), 10)

            for instance in values_instances:
                values_description = []
                for variable in variables:
                    values_description.append(dict(
                        name=variable.name,
                        type=type(variable.dub).__name__,
                        value=variable.dub.to_str(instance[variable.name])
                    ))

                result.append(dict(
                    text=case.resulting_template.utter(instance).to_str(),
                    intent=intent,
                    values=values_description,
                    language=case.target_language_code,
                ))

        return result
