from dataclasses import dataclass, field
from .test_report_item import TestReportItem

@dataclass
class TestReportSection:
    caption: str = None
    comment: str|None = None
    items: list[TestReportItem] = field(default_factory=list)


