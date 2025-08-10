from typing import *
from ..dubs import DictTemplateDub, DataclassTemplateDub, VariableDub, TemplateDub, DubParameters, SequenceDub, IDub
from ..globalization import LanguageDispatchDub
from copy import copy, deepcopy
from foundation_kaia.prompters import Prompter
from dataclasses import dataclass
from .template_base import TemplateBase


@dataclass
class TemplateContext:
    context: Prompter|None = None
    reply_to: Tuple['Template',...] = None
    reply_details: Prompter|None = None


def _create_dub(args, kwargs, factory):
    language_to_sequences = {}
    for key, sequence in kwargs.items():
        language = key.split('_')[0]
        if language not in language_to_sequences:
            language_to_sequences[language] = []
        language_to_sequences[language].append(sequence)
    if len(args) > 0:
        if DubParameters.default_language() in language_to_sequences:
            raise ValueError(f"definitions for default language {DubParameters.default_language()} are present in args and kwargs at the same time")
        language_to_sequences[DubParameters.default_language()] = args
    templates = {language: factory(*sequence) for language, sequence in language_to_sequences.items()}
    return LanguageDispatchDub(**templates)


class Template(TemplateBase[LanguageDispatchDub[TemplateDub]]):
    def __init__(self, *args: str, **kwargs: str):
        self._args = args
        self._kwargs = kwargs
        self._type = None
        super().__init__(_create_dub(args, kwargs, DictTemplateDub))

    def get_language_to_sequences(self) -> dict[str,tuple[SequenceDub,...]]:
        return {language: dub.sequences for language, dub in self.dub.dispatch.items()}


    def with_type(self, _type: Type) -> 'Template':
        obj = self.clone()
        obj._type = _type
        obj._dub = _create_dub(self._args, self._kwargs, lambda *seq: DataclassTemplateDub(_type, *seq))
        return obj


    def substitute(self, **new_dubs: VariableDub) -> 'Template':
        obj = self.clone()

        language_to_new_sequences = {}
        for language, sequences in self.get_language_to_sequences().items():
            new_sequences = []
            for sequence in sequences:
                new_sequence = []
                for element in sequence.sequence:
                    if isinstance(element, VariableDub) and element.name in new_dubs:
                        new_element = new_dubs[element.name]
                        if isinstance(new_element, VariableDub):
                            pass
                        elif isinstance(new_element, IDub):
                            new_element = VariableDub(element.name, new_element, element.description)
                        else:
                            raise ValueError(f"Replacement for {element.name} must be VariableDub or IDub")
                        element = new_element
                    new_sequence.append(copy(element))
                new_sequences.append(SequenceDub(tuple(new_sequence)))
            language_to_new_sequences[language] = new_sequences

        kwargs = {f'{language}_{index}': sequence for language, sequences in language_to_new_sequences.items() for index, sequence in enumerate(sequences)}
        template = Template(**kwargs)
        if self._type is not None:
            template = template.with_type(self._type)
        obj._dub = template.dub
        return obj

    def _get_single_attached_subdub_name(self) -> str|None:
        found_name = None
        for language, sequences in self.get_language_to_sequences().items():
            for sequence in sequences:
                variables = sequence.get_variables()
                if len(variables)>1:
                    return None
                if len(variables)==0:
                    continue
                if found_name is None:
                    found_name = variables[0].name
                elif found_name != variables[0].name:
                    return None
        return found_name

    def __str__(self):
        template = self.dub.get_dispatch(DubParameters())
        return 'Template: '+ ' | '.join(s.get_human_readable_representation(DubParameters()) for s in template.sequences)

