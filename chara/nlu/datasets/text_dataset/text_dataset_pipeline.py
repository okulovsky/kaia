from chara.paraphrasing.common import Paraphrase, ParsedTemplate, generate_values_for_variables
from pathlib import Path
from grammatron import Template, OptionsDub, VariableDub
from chara.common import Chara, CaseCollection
from chara.common.llm import BrainBoxLLMEngine, LLMSetup


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
        return self.export(self.paraphrase(), 10)

    def paraphrase(self) -> list[TextDatasetCase]:
        cases = []
        for mood in self.moods:
            for language in self.languages:
                for template in self.templates:
                    cases.append(TextDatasetCase(template, language, mood))
        setup = LLMSetup(BrainBoxLLMEngine(), self.model)
        settings = Paraphrase.Settings(
            paraphrase_request=setup.default().template(Path(__file__).parent / "template_prompt.jinja").to_request(),
            enable_words_translation=True,
            grammar_correction_attempts=3,
            words_translation_attempts=3,
            enable_options_expanding=True,
            enable_option_values_translation=False,
        )
        pipe = Paraphrase.Pipeline(settings)
        paraphrase_results = Chara.call(pipe)(CaseCollection(cases))
        return list(paraphrase_results.successes)

    @staticmethod
    def export(cases, variants_count: int) -> list[dict]:
        result = []
        for case in cases:
            intent = case.original_template.get_name()
            variables = ParsedTemplate.parse_single(case.resulting_template).variables
            # The values of the options are written as the original template has them, whatever the language of the text
            original_options = {
                leaf.name: leaf.dub
                for template_dub in case.original_template.dub.dispatch.values()
                for sequence in template_dub.sequences
                for leaf in sequence.get_leaves()
                if isinstance(leaf, VariableDub) and isinstance(leaf.dub, OptionsDub)
            }
            if len(variables) == 0:
                values_instances = [{}]
            else:
                values_instances = generate_values_for_variables(list(variables), variants_count)

            for instance in values_instances:
                values_description = []
                for variable in variables:
                    value = instance[variable.name]
                    dub = original_options.get(variable.name)
                    # Options added by OptionExpanding are not in the original template and stay as they are said
                    if dub is None or value not in dub.value_to_strs:
                        dub = variable.dub
                    values_description.append(dict(
                        name=variable.name,
                        type=type(variable.dub).__name__,
                        value=dub.to_str(value)
                    ))

                result.append(dict(
                    text=case.resulting_template.utter(instance).to_str(),
                    intent=intent,
                    values=values_description,
                    language=case.target_language_code,
                ))

        return result
