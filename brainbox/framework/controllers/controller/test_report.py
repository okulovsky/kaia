import json
from typing import *
from dataclasses import dataclass
from ...common import File

class TestReport:
    @dataclass
    class Item:
        header_level: int|None = None
        text_content: str|None = None
        file_content: File|None = None
        is_code: bool = False

    def __init__(self,
                 name: str,
                 items: Iterable['TestReport.Item'],
                 error: str|None
                 ):
        self.name = name
        self.items = tuple(items)
        self.error = error

    @staticmethod
    def H1(header: str):
        return TestReport.Item(header_level=0, text_content=header)

    @staticmethod
    def H2(header: str):
        return TestReport.Item(header_level=1, text_content=header)

    @staticmethod
    def H3(header: str):
        return TestReport.Item(header_level=2, text_content=header)

    @staticmethod
    def H4(header: str):
        return TestReport.Item(header_level=3, text_content=header)

    @staticmethod
    def text(text: str):
        return TestReport.Item(text_content=text)

    @staticmethod
    def file(file: File):
        return TestReport.Item(file_content=file)

    @staticmethod
    def json(data: Any):
        return TestReport.Item(text_content=json.dumps(data, indent=2), is_code=True)

    @staticmethod
    def code(code: str):
        return TestReport.Item(text_content=code, is_code=True)


