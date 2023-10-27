from typing import *
from .dto import DubbingSequence, DubbingFragment
from copy import copy

def _finish_sequence(sequence):
    t = sequence.get_text()
    debt = None
    if t.strip()[-1] not in  '.?!':
        debt = '. '
    elif t[-1]!=' ':
        debt = ' '
    if debt is not None:
        last_frag = copy(sequence.fragments[-1])
        last_frag.suffix+=debt
        return DubbingSequence(sequence.fragments[:-1]+(last_frag,)) #We could also place debt as a separate placeholder fragment, but this positioning improves quality
    return sequence


def _merge(sequence_1, sequence_2):
    sequence_2 = _finish_sequence(sequence_2)
    return DubbingSequence(sequence_1.fragments+sequence_2.fragments)


def optimize_sequences(sequences: List[DubbingSequence], max_length = 80, min_length = 20):
    result = [] #type: List[DubbingSequence]
    for sequence in sequences:
        ln = len(sequence.get_text())
        found = False
        for i in range(len(result)):
            if len(result[i].get_text()) + ln + 2 < max_length:
                result[i] = _merge(result[i], sequence)
                found = True
                break
        if not found:
            result.append(_finish_sequence(sequence))

    result_2 = []
    for sequence in result:
        if len(sequence.get_text()) < min_length:
            result_2.append(_merge(sequence, DubbingSequence((DubbingFragment('', 'And they lived happily ever after', True),))))
        else:
            result_2.append(sequence)

    return result_2

