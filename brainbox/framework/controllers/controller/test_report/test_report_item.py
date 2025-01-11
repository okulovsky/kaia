import os.path
from typing import *
from dataclasses import dataclass, field
from ....common import File

@dataclass
class TestReportItem:
    decider: str
    method: str | None
    parameter: str | None
    arguments: dict
    result: Any
    href: str|None = None
    comment: str | None = None
    result_is_file: bool = False
    result_is_array_of_files: bool = False
    uploaded_files: dict[str, File] = field(default_factory=dict)
    used_resources: dict[str, File] = field(default_factory=dict)



class TestReportItemHolder:
    def __init__(self, api, item: TestReportItem):
        self.item = item
        self.api = api


    def with_comment(self, comment: str):
        self.item.comment = comment
        return self

    def result_is_file(self, kind: File.Kind | None = None):
        self.item.result = self.api.open_file(self.item.result)
        if kind is not None:
            if self.item.result.kind != kind:
                raise ValueError(f"Expected kind {kind}, but was {self.item.result.kind}")
        self.item.result_is_file = True
        return self

    def result_is_array_of_files(self, kind: File.Kind | None = None):
        self.item.result = [self.api.open_file(r) for r in self.item.result]
        if kind is not None:
            for r in self.item.result:
                if r.kind != kind:
                    raise ValueError(f"Expected kind {kind}, but was {r.kind}")
        self.item.result_is_array_of_files = True
        return self

    def with_uploaded_file(self, fname: str, file: File):
        self.item.uploaded_files[fname] = file
        return self

    def with_resources(self, decider: Type, path: str):
        lst = self.api.controller_api.list_resources(decider, path)
        for file in lst:
            self.item.used_resources[file] = self.api.controller_api.download_resource(decider, file)
        return self

    def href(self, href: str):
        self.item.href = href
        return self