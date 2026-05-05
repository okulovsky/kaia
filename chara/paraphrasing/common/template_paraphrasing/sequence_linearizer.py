from dataclasses import dataclass, field
from grammatron import (
    VariableDub, IDub, ConstantDub,
    ISubSequenceDub, PluralAgreement, IPluralAgreement, GrammarAdoptableDub
)
from .fragment_descriptors import IFragmentDescriptor, VariableFragmentDescriptor, PluralAgreementWithVariable, PluralAgreementWithConstant

@dataclass
class LinearizedFragment:
    dub: IDub
    descriptor: IFragmentDescriptor|None = None
    string_fragment: str|None = None


@dataclass
class SequenceLinearizer:
    fragments: list[LinearizedFragment] = field(default_factory=list)

    def linearize(self, sequence: ISubSequenceDub, parameters):
        if isinstance(sequence, ConstantDub):
            self.fragments.append(LinearizedFragment(
                sequence,
                string_fragment=sequence.value
            ))
        elif isinstance(sequence, VariableDub):
            self.fragments.append(LinearizedFragment(
                sequence,
                descriptor=VariableFragmentDescriptor(sequence)
            ))
        elif isinstance(sequence, PluralAgreement):
            pa = sequence.get_dispatch(parameters)
            if not isinstance(pa, IPluralAgreement):
                raise ValueError("Inside PluralAgreement, IPluralAgreement is expected")
            if isinstance(pa.entity, VariableDub):
                self.fragments.append(LinearizedFragment(
                    sequence,
                    PluralAgreementWithVariable(pa.amount, pa.entity)
                ))
            elif isinstance(pa.entity, GrammarAdoptableDub):
                self.fragments.append(LinearizedFragment(
                    sequence,
                    PluralAgreementWithConstant(pa.amount, pa.entity)
                ))
            else:
                raise ValueError(f"pa.entity must be Variable of GrammarAdoptable, but was {pa.entity}")
        else:
            subs = sequence.get_sequence()
            if subs is None:
                raise ValueError("sequence was primitive, but not of a supported type")
            else:
                for s in subs:
                    self.linearize(s, parameters)