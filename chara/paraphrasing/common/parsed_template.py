from dataclasses import dataclass, field
from grammatron import (
    Template, TemplateDub, SequenceDub, VariableDub, IDub, ConstantDub,
    ISubSequenceDub, PluralAgreement, DubParameters, IPluralAgreement, GrammarAdoptableDub
)
from avatar.daemon.paraphrase_service import ParaphraseRecord
import re
from collections import OrderedDict

@dataclass
class FragmentDescription:
    dub: IDub
    description: str

@dataclass
class UnwrappedSequence:
    fragments: list[str] = field(default_factory=list)
    fragment_to_description: OrderedDict[str, FragmentDescription] = field(default_factory=OrderedDict)

    def _add(self, fragment, dub: IDub, *docs: VariableDub|str):
        self.fragments.append(fragment)
        description = []
        for d in docs:
            if isinstance(d, str):
                description.append(d)
            elif isinstance(d, VariableDub):
                description.append(f"Variable `{d.name}`" + (f": {d.description}." if d.description is not None else '.'))
        self.fragment_to_description[fragment] = FragmentDescription(dub, f'* {fragment}. '+' '.join(description))

    def run(self, sequence: ISubSequenceDub, parameters):
        if isinstance(sequence, ConstantDub):
            self.fragments.append(sequence.value)
        elif isinstance(sequence, VariableDub):
            self._add('{'+sequence.name+'}', sequence, "", sequence)
        elif isinstance(sequence, PluralAgreement):
            pa = sequence.get_dispatch(parameters)
            if not isinstance(pa, IPluralAgreement):
                raise ValueError("Inside PluralAgreement, IPluralAgreement is expected")
            if isinstance(pa.entity, VariableDub):
                self._add('{'+pa.amount.name+'+'+pa.entity.name+'}', sequence, f"Two variables, set in a grammatically correct form.", pa.amount, pa.entity)
            elif isinstance(pa.entity, GrammarAdoptableDub):
                self._add('{'+pa.amount.name+'/' + pa.entity.value +'}', sequence, pa.amount, f"Then, word `{pa.entity.value}` is added in a grammatically correct form.")
            else:
                raise ValueError(f"pa.entity must be Variable of GrammarAdoptable, but was {pa.entity}")
        else:
            subs = sequence.get_sequence()
            if subs is None:
                raise ValueError("sequence was primitive, but not of a supported type")
            else:
                for s in subs:
                    self.run(s, parameters)

@dataclass
class ParsedSequence:
    sequence_index: int
    sequence: SequenceDub
    unwrapped_sequence: UnwrappedSequence
    representation: str


@dataclass
class ParsedTemplate:
    template: Template
    language: str
    template_dub: TemplateDub
    variables: list[VariableDub]
    variables_tag: str
    sequences: list[ParsedSequence] = field(default_factory=list)


    @staticmethod
    def parse(template: Template) -> tuple['ParsedTemplate',...]:
        result: dict[tuple[str,str], ParsedTemplate] = {}
        for language, template_dub in template.dub.dispatch.items():
            for sequence_index, sequence in enumerate(template_dub.sequences):
                unwrapped = UnwrappedSequence()
                unwrapped.run(sequence, DubParameters(language=language))
                variables = [v for v in sequence.get_leaves() if isinstance(v, VariableDub)]
                variables_tag = ParaphraseRecord.create_variables_tag(v.name for v in variables)

                key = (language,variables_tag)
                if variables_tag not in result:
                    result[key] = ParsedTemplate(
                        template,
                        language,
                        template_dub,
                        variables,
                        variables_tag,
                    )

                result[key].sequences.append(ParsedSequence(
                    sequence_index,
                    sequence,
                    unwrapped,
                    ''.join(unwrapped.fragments)
                ))
        templates = tuple(v for _, v in result.items())
        return templates


    def restore_template(self, s: str) -> Template:
        unwrapped_sequence = self.sequences[0].unwrapped_sequence
        regexp = r'(\{[^\}]*\})'
        hit_fragments = set(unwrapped_sequence.fragment_to_description)
        sequence = []
        for fragment in re.split(regexp, s):
            if len(fragment)==0:
                continue
            if fragment[0] == '{':
                if fragment not in unwrapped_sequence.fragment_to_description:
                    raise ValueError(f"Fragment `{fragment}` is missing from the original template")
                else:
                    hit_fragments.remove(fragment)
                    sequence.append(unwrapped_sequence.fragment_to_description[fragment].dub)
            else:
                sequence.append(ConstantDub(fragment))
        if len(hit_fragments) != 0:
            raise ValueError(f"Some fragments from the original template were not used: {hit_fragments}")

        argument = SequenceDub(tuple(sequence))

        template = Template(argument).with_name(self.template.get_name())
        if self.template.get_type() is not None:
            template = template.with_type(self.template.get_type())
        template._context = self.template.get_context()
        return template






