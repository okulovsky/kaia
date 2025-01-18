from typing import *
from .test_report_item import TestReportItem, TestReportItemHolder
from .test_report_section import TestReportSection
from .main_section_content import MainSectionContent
from .source_file_attachment import SourceFileAttachment
import inspect
from yo_fluq import FileIO


def make_hierarchy(name: str, items: list) -> list[TestReportSection]:
    sections = [TestReportSection(name)]
    for item in items:
        if isinstance(item, TestReportSection):
            sections.append(item)
        elif isinstance(item, MainSectionContent):
            sections[0].comment = item.comment
        elif isinstance(item, TestReportItemHolder):
            sections[-1].items.append(item.item)
        elif isinstance(item, SourceFileAttachment):
            pass
        else:
            raise ValueError(f"Unexpected type of item in report\n{item}")
    return sections


def assemble_code_files(items: list, controller_type: Type):
    source_codes = []
    for item in items:
        if isinstance(item, SourceFileAttachment):
            source_codes.append(FileIO.read_text(inspect.getfile(item.method_or_type)))
    if len(source_codes) == 0:
        source_codes.append(inspect.getsource(getattr(controller_type,'_self_test_internal')))
    return source_codes




class TestReport:
    def __init__(self,
                 name: str,
                 items: Iterable[Union[TestReportItemHolder, TestReportSection]],
                 error: str|None,
                 controller_type: Type
                 ):
        items = list(items)
        self.name = name
        self.sections: list[TestReportSection] = make_hierarchy(name, items)
        self.error = error
        self.source_codes = assemble_code_files(items, controller_type)


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
                job.accepted_timestamp,
                job.finished_timestamp,
        ))

    @staticmethod
    def section(caption: str, comment: str|None = None):
        return TestReportSection(caption, comment)

    @staticmethod
    def main_section_content(comment: str):
        return MainSectionContent(comment)

    @staticmethod
    def attach_source_file(method_or_class: Any):
        return SourceFileAttachment(method_or_class)


