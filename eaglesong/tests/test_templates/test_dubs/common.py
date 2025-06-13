from typing import *
from eaglesong.templates.dubs import *
from unittest import TestCase


def run_regex_integration_test(tc,
         template: IDub,
         values: Iterable,
         parameters: Iterable[DubParameters] | None = None,
         debug: bool = False
         ):
    if parameters is None:
        parameters = [DubParameters(spoken=True), DubParameters(spoken=False)]

    for p in parameters:
        parser = RegexParser(template, p)
        for value in values:
            if debug:
                print(f"VALUE {value}")
            s = template.to_str(value, p)
            if debug:
                print(f'STR {s}')
            restored_value = parser.parse(s)
            if debug:
                print(f'RESULT {restored_value}')
                print('\n')
            tc.assertEqual(value, restored_value)