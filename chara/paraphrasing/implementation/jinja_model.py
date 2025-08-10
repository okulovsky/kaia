from collections import defaultdict

from grammatron import *
from dataclasses import dataclass
from .parsed_template import ParsedTemplate
from yo_fluq_ds import *


@dataclass
class JinjaModel:
    template: ParsedTemplate
    samples: tuple[str,...]
    variables_description: tuple[str,...]
    context: TemplateContext

    has_description: bool = False
    has_context: bool = False
    reply_to_examples: tuple[str,...]|None = None

    def __post_init__(self):
        self.context = self.template.template.get_context()
        self.has_description = len(self.variables_description) > 0
        self.has_context = (
                self.context.context is not None
                or self.context.reply_to is not None
                or self.context.reply_details is not None
        )

        if self.context.reply_to is not None:
            self.reply_to_examples = tuple(
                parsed.representation
                for template in self.context.reply_to
                for parsed in ParsedTemplate.parse(template)
            )


    @staticmethod
    def parse_from_template(template: Template) -> tuple['JinjaModel',...]:
        parsed = ParsedTemplate.parse(template)
        group_to_templates = defaultdict(list)
        for parse in parsed:
            group_to_templates[(parse.language, parse.variables_tag)].append(parse)

        result = []
        for group in group_to_templates.values():
            group = cast(list[ParsedTemplate], group)
            samples = tuple(g.representation for g in group)
            template = group[0]



            result.append(JinjaModel(
                template,
                samples,
                tuple(c.description for c in template.unwrapped_sequence.fragment_to_description.values()),
                template.template.get_context(),
                ))

        return tuple(result)






