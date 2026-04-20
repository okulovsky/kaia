from grammatron import SequenceDub, VariableDub, DubParameters, IDub, Template, TemplateDub, ConstantDub
from avatar.daemon import ParaphraseRecord
from .sequence_linearizer import SequenceLinearizer
from .fragment_descriptors import IFragmentDescriptor
from .value_generator import generate_values_for_variables
from dataclasses import dataclass
import re

EXAMPLES_PER_FRAGMENT = 2
EXAMPLES_COUNT = 5

@dataclass
class Fragment:
    name: str
    description: str
    dub: IDub
    descriptor: IFragmentDescriptor
    examples: tuple[str,...]

@dataclass
class ParsedTemplate:
    sequence: SequenceDub
    variables: tuple[VariableDub, ...]
    variables_tag: str
    representation: str
    fragments: tuple[Fragment,...]
    fragments_tag: str
    original_language: str = ''
    original_template: Template = None
    original_template_dub: TemplateDub = None
    original_sequence_dub: SequenceDub = None
    alternatives: 'tuple[ParsedTemplate,...]' = ()

    def restore_template(self, s: str, target_language: str) -> Template:
        regexp = r'(\{[^\}]*\})'
        required_fragments = [f.name for f in self.fragments]
        hit_fragments = set(required_fragments)
        sequence = []
        for fragment in re.split(regexp, s):
            if len(fragment)==0:
                continue
            if fragment[0] == '{':
                if fragment not in required_fragments:
                    raise ValueError(f"Fragment `{fragment}` is missing from the original template. Available are {required_fragments}")
                else:
                    hit_fragments.remove(fragment)
                    dub = next((f for f in self.fragments if f.name == fragment)).dub
                    sequence.append(dub)
            else:
                sequence.append(ConstantDub(fragment))
        if len(hit_fragments) != 0:
            raise ValueError(f"Some fragments from the original template were not used: {hit_fragments}")

        argument = SequenceDub(tuple(sequence))

        template = Template(**{target_language: argument}).with_name(self.original_template.get_name())
        if self.original_template.get_type() is not None:
            template = template.with_type(self.original_template.get_type())
        template._context = self.original_template.get_context()
        return template

    @staticmethod
    def parse(template: Template) -> 'list[ParsedTemplate]':
        result: dict[tuple[str, str], list[ParsedTemplate]] = {}
        for language, template_dub in template.dub.dispatch.items():
            for sequence_index, sequence in enumerate(template_dub.sequences):
                parsed_sequence = ParsedTemplate._construct(sequence, DubParameters(language=language))
                parsed_sequence.original_language = language
                parsed_sequence.original_sequence_dub = sequence
                parsed_sequence.original_template = template
                parsed_sequence.original_template_dub = template_dub
                key = (language, parsed_sequence.fragments_tag)
                if key not in result:
                    result[key] = []
                result[key].append(parsed_sequence)
        final_result = []
        for key, sequences in result.items():
            sequence = sequences[0]
            sequence.alternatives = tuple(sequences[1:])
            final_result.append(sequence)
        return final_result

    @staticmethod
    def parse_single(template: Template) -> 'ParsedTemplate':
        result = ParsedTemplate.parse(template)
        if len(result) != 1:
            raise ValueError("Expected exactly one sequence")
        return result[0]

    @staticmethod
    def _construct(sequence: SequenceDub, parameters: DubParameters):
        variables = [v for v in sequence.get_leaves() if isinstance(v, VariableDub)]
        variables_tag = ParaphraseRecord.create_variables_tag(v.name for v in variables)
        linearizer = SequenceLinearizer()
        linearizer.linearize(sequence, parameters)
        fragments = {f.descriptor.get_representation() : f for f in linearizer.fragments if f.descriptor is not None}

        example_values = generate_values_for_variables(variables, EXAMPLES_COUNT)
        fragment_to_examples: dict[str, list[str]] = { f: [] for f in fragments }
        for example in example_values:
            debug_parameters = parameters.change_debug(True)
            sequence.to_str(example, debug_parameters)
            for fragment_name, fragment in fragments.items():
                fragment_to_examples[fragment_name].append(fragment.dub.debug_to_str_result)

        final_fragments = []
        for fragment_name in list(fragment_to_examples):
            raw = fragments[fragment_name]
            examples = list(set(fragment_to_examples[fragment_name]))
            example_str = ', '.join('"'+e+'"' for e in examples[:EXAMPLES_PER_FRAGMENT])
            description = raw.descriptor.get_description(example_str)

            final_fragment = Fragment(
                fragment_name,
                description,
                raw.dub,
                raw.descriptor,
                tuple(examples)
            )
            final_fragments.append(final_fragment)

        representation = []
        for l in linearizer.fragments:
            if l.descriptor is None:
                representation.append(l.string_fragment)
            else:
                representation.append(l.descriptor.get_representation())

        return ParsedTemplate(
            sequence,
            tuple(variables),
            variables_tag,
            ''.join(representation),
            tuple(final_fragments),
            '/'.join(f.name for f in final_fragments)
        )




















