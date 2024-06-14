from typing import *
from .brainbox_test_cases import BrainBoxTestCase, BrainBoxTestCaseReportSection
from ..core import BrainBoxWebApi
from uuid import uuid4
import time

def execute_tests(tests: Iterable[BrainBoxTestCase], api: BrainBoxWebApi):
    batch = str(uuid4())

    name_to_tasks = {}
    name_to_test = {}
    for test in tests:
        tasks = tuple(test.generate_tasks())
        name_to_tasks[test.get_name()] = tasks
        name_to_test[test.get_name()] = test
        for task in tasks:
            task.batch = batch
            api.add(task)


    while True:
        summary = api.get_summary(batch)
        done = sum(s['finished'] for s in summary)
        print(f'\r{100*done/len(summary)}               ', end='')

        if done == len(summary):
            break
        time.sleep(1)

    result = {}
    for name, tasks in name_to_tasks.items():
        result[name] = name_to_test[name].validate_and_get_report_section(tasks, api)

    return result


def draw_results(sections: Dict[str, BrainBoxTestCaseReportSection], cases: Iterable[BrainBoxTestCase]):
    from ipywidgets import HTML, VBox

    cases_dict = {tc.get_name(): tc for tc in cases}
    ar = []
    for name, section in sections.items():
        ar.append(HTML(f'<b>{name}</b>'))
        ar.append(cases_dict[name].draw_section(section))
    return VBox(ar)



