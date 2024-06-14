from yo_fluq_ds import *
from kaia.infra import Loc

def length_filter(s):
    return len(s) <= 100 and len(s) >= 80


def no_bad_symbols(s):
    bad_symbols = '!?…:;"'
    for b in bad_symbols:
        if b in s:
            return False
    return True


def not_too_much_capital_letters(s):
    ss = s.lower()
    cnt = 0
    for c1, c2 in zip(s, ss):
        if c1 != c2:
            cnt += 1
    return cnt < 4


def filter_file(path):
    lines = (
        Query.file.text(path)
        .select(lambda z: z.strip())
        .where(length_filter)
        .where(no_bad_symbols)
        .where(not_too_much_capital_letters)
        .to_list()
    )
    return lines

