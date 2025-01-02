from typing import *
from .test_report_item import TestReportItem, TestReportItemHolder
from .test_report_section import TestReportSection
from .main_section_content import MainSectionContent

def make_hierarchy(name: str, items: Iterable) -> list[TestReportSection]:
    sections = [TestReportSection(name)]
    for item in items:
        if isinstance(item, TestReportSection):
            sections.append(item)
        elif isinstance(item, MainSectionContent):
            sections[0].comment = item.comment
        elif isinstance(item, TestReportItemHolder):
            sections[-1].items.append(item.item)
        else:
            raise ValueError(f"Unexpected type of item in report\n{item}")
    return sections





class TestReport:
    def __init__(self,
                 name: str,
                 items: Iterable[Union[TestReportItemHolder, TestReportSection]],
                 error: str|None
                 ):
        self.name = name
        self.sections: list[TestReportSection] = make_hierarchy(name, items)
        self.error = error


    @staticmethod
    def last_call(brain_box_api) -> TestReportItemHolder:
        from ....brainbox import BrainBoxApi
        api: BrainBoxApi = brain_box_api
        summary = api.summary()
        recent_id = list(sorted(summary, key=lambda z: z['received_timestamp'], reverse=True))[0]['id']
        job = api.job(recent_id)
        return TestReportItemHolder(
            api,
            TestReportItem(
            job.decider,
            job.method,
            job.decider_parameter,
            job.arguments,
            job.result,
        ))

    @staticmethod
    def section(caption: str, comment: str|None = None):
        return TestReportSection(caption, comment)

    @staticmethod
    def main_section_content(comment: str):
        return MainSectionContent(comment)

