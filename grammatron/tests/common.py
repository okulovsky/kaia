from typing import *
from grammatron import *
from unittest import TestCase
from yo_fluq_ds import *


def run_regex_integration_test(tc: TestCase,
         template: IDub,
         values: Iterable,
         parameters: Iterable[DubParameters] | None = None,
         debug: bool = False
         ):
    if parameters is None:
        parameters = Query.combinatorics.grid(spoken=[True, False], language=['en','ru']).select(lambda z: DubParameters(**z)).to_list()

    for p in parameters:
        with tc.subTest(f'{p.spoken}/{p.language}'):
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