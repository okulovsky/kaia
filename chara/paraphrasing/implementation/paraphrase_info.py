from eaglesong.templates import *
from dataclasses import dataclass
from eaglesong.templates import ConstantDub, VariableDub, IGrammarAdoptionDub
import re

@dataclass
class ParaphraseInfo:
    template_name: str
    template_type: type|None
    index_to_samples: dict[int, str]
    fragment_to_dub: dict[str, ConstantDub|VariableDub|IGrammarAdoptionDub]
    context: TemplateContext
    variables: set[str]
    variables_to_description: dict[str, str]

    has_variables_to_description: bool = False
    has_variables: bool = False
    has_grammar_adoptions: bool = False
    has_context: bool = False
    reply_to_examples: tuple[str,...]|None = None
    samples: tuple[str,...]|None = None

    def __post_init__(self):
        self.has_variables_to_description = len(self.variables_to_description) > 0
        self.has_variables = len([v for v in self.fragment_to_dub.values() if isinstance(v, VariableDub)]) > 0
        self.has_grammar_adoptions = len([v for v in self.fragment_to_dub.values() if isinstance(v, IGrammarAdoptionDub)]) > 0
        self.has_context = (
                self.context.context is not None
                or self.context.reply_to is not None
                or self.context.reply_details is not None
        )

        if self.context.reply_to is not None:
            self.reply_to_examples = tuple(
                s
                for template in self.context.reply_to
                for s in template.string_templates
            )
        self.samples = tuple(self.index_to_samples.values())

    @staticmethod
    def parse_from_template(template: Template) -> tuple['ParaphraseInfo',...]:
        if not isinstance(template.dub, TemplateDub):
            raise ValueError('dub is expected to be TemplateDub')

        key_to_index = {}
        for index, s in enumerate(template.dub.sequences):
            fragments = s.to_human_readable_string_fragments()
            fragments = [s.representation for s in fragments if not isinstance(s.template_sequence_part, ConstantDub)]
            key = tuple(sorted(set(fragments)))
            if key not in key_to_index:
                key_to_index[key] = []
            key_to_index[key].append(index)

        description = {s.name: s.description for s in template.attached_variables.values()}
        sequences: list[TemplateSequenceDub] = list(template.dub.sequences)

        result = []
        for key, indices in key_to_index.items():
            fragments = sequences[0].to_human_readable_string_fragments()
            fragments = [f for f in fragments if not isinstance(f.template_sequence_part, ConstantDub)]

            variables = set(f.template_sequence_part.variable.name for f in fragments if isinstance(f.template_sequence_part, VariableDub))
            index_to_sample = {index:sequences[index].to_human_readable_string() for index in indices}

            result.append(ParaphraseInfo(
                template.get_name(),
                template.get_type(),
                index_to_sample,
                {f.representation:f.template_sequence_part for f in fragments},
                template.get_context(),
                variables,
                {k:v for k,v in description.items() if k in variables and v is not None}
            ))

        return tuple(result)

    def restore_template(self, s: str) -> Template:
        regexp = r'(\{[^}]*\}|\[[^\]]*\])'
        hit_fragments = set(self.fragment_to_dub)
        sequence = []
        for fragment in re.split(regexp, s):
            if len(fragment)==0:
                continue
            if fragment[0] == '[' or fragment[0] == '{':
                if fragment not in self.fragment_to_dub:
                    raise ValueError(f"Fragment `{fragment}` is missing from the original template")
                else:
                    hit_fragments.remove(fragment)
                    dub = self.fragment_to_dub[fragment]
                    if isinstance(dub, VariableDub):
                        sequence.append(str(dub.variable))
                    elif isinstance(dub, IGrammarAdoptionDub):
                        sequence.append(str(dub.as_variable()))
                    else:
                        raise ValueError("Expected VariableDub or IGrammarAdoptionDub")
            else:
                sequence.append(fragment)
        if len(hit_fragments) != 0:
            raise ValueError(f"Some fragments from the original template were not used: {hit_fragments}")

        argument = ''.join(sequence)
        template = Template(argument).with_name(self.template_name)
        if self.template_type is not None:
            template = template.with_type(self.template_type)
        template._context = self.context
        return template





