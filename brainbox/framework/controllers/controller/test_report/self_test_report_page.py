import json
import re

from .test_report import TestReport
from .test_report_item import TestReportItem
from ....common import File, HTML
import base64


class Builder:
    def __init__(self):
        self.html = []

    def replace_code(self, code):
        return HTML.escape_code(code)


    def add_code(self, code, style=''):
        code = self.replace_code(code)
        self.html.append(f'<p style="font-family: monospace; {style}">{code}</p>')

    def error_color_style(self):
        return 'color: #dd0000;'

    def add_file(self, file_content: File):
        if not isinstance(file_content, File):
            self.html.append(f"<p {self.error_color_style()}>Expected File, but was:</p>")
            self.add_code(str(file_content), self.error_color_style())
            return
        if file_content.kind == File.Kind.Json or file_content.kind == File.Kind.Text:
            self.add_code(file_content.string_content)
        elif file_content.kind == File.Kind.Audio:
            b64 = base64.b64encode(file_content.content).decode("utf-8")
            html=f'''
            <audio controls>
                <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
                    <p {self.error_color_style()}>Your browser does not support the audio element.</p>
            </audio>'''
            self.html.append(html)
        elif file_content.kind == File.Kind.Image:
            b64 = base64.b64encode(file_content.content).decode("utf-8")
            img_tag = f'<img src="data:;base64,{b64}">'
            self.html.append(img_tag)
        else:
            self.html.append(f'<p {self.error_color_style()}>File.Kind {file_content.kind} is not yet supported</p>')

    def add_files_dict(self, header, d: dict[str, File]):
        if len(d) > 0:
            self.html.append(f"<h3>{header}</h3>")
            for key, value in d.items():
                self.html.append(f"<h4>{key}</h4>")
                self.add_file(value)

    def process_item(self, item: TestReportItem):
        self.html.append('<h2')
        if item.href is not None:
            self.html.append(f' id="{item.href}"')
        self.html.append('>')

        self.html.append(item.decider)
        if item.method is not None:
            self.html.append(f"::{item.method}")
        if item.parameter is not None:
            self.html.append(f' ({item.parameter})')
        self.html.append("</h2>")

        if item.finished_timestamp is not None and item.accepted_timestamp is not None:
            self.html.append("<p>")
            self.html.append( str( (item.finished_timestamp - item.accepted_timestamp).total_seconds()) +" sec")
            self.html.append("</p>")

        if item.comment is not None:
            self.html.append("<p>")
            self.html.append(item.comment)
            self.html.append("</p>")
        self.html.append("<h3>Arguments</h3>")
        for key, value in item.arguments.items():
            self.html.append(f'<h4>{key}</h4>')
            if isinstance(value, File):
                self.html.append("<i>File</i><br>")
                self.add_file(value)
            elif isinstance(value, list) or isinstance(value, dict):
                self.add_code(json.dumps(value, indent=2))
            else:
                self.add_code(str(value))

        self.add_files_dict("Uploaded files", item.uploaded_files)
        self.add_files_dict("Used resources", item.used_resources)

        self.html.append("<h3>Result</h3>")
        if item.result_is_file:
            self.html.append("<i>File</i><br>")
            self.add_file(item.result)
        elif item.result_is_array_of_files:
            self.html.append("<i>Array of files</i><br>")
            for file in item.result:
                self.add_file(file)
        elif isinstance(item.result, list) or isinstance(item.result, dict):
            self.add_code(json.dumps(item.result, indent=2))
        else:
            self.add_code(str(item.result))

    def process_source_code(self, code: str):
        pattern = r"\.href\((['\"])(.*?)\1\)"
        self.html.append('<p style="font-family: monospace;">')
        for line in code.split('\n'):
            line = self.replace_code(line)
            self.html.append(line)
            match = re.search(pattern, line)
            if match is not None:
                self.html.append(f'<a href="#{match.group(2)}">[→]</a>')
            self.html.append("<br>")


    def build(self, report: TestReport):
        self.html.append(f'<h1>Test source code</h1>')
        for index, code in enumerate(report.source_codes):
            if code is None:
                raise ValueError(f"Code is none at index {index}")
            self.process_source_code(code)


        for section in report.sections:
            self.html.append(f'<h1>{section.caption}</h1>')
            if section.comment is not None:
                self.html.append(f'<p>{section.comment}</p>')
            for item in section.items:
                self.process_item(item)

        if report.error is not None:
            self.html.append(f"<h1 {self.error_color_style()}><b>Exception</b></h1>")
            self.add_code(report.error, self.error_color_style())

        for i in range(len(self.html)):
            if self.html[i] is None:
                print(self.html[max(0,i-5):min(len(self.html), i+5)])
                raise ValueError(f"None in html at index {i}")
        return "<html><body>"+"".join(self.html)+"</body></html>"





def create_self_test_report_page(report: TestReport):
    builder = Builder()
    return builder.build(report)