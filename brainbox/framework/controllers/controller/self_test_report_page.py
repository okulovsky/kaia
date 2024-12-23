from .test_report import TestReport
from ...common import File
import base64

class Builder:
    def __init__(self):
        self.html = []

    def make_code(self, code, style=''):
        code = (
            code
            #.replace("<", "&lt;")
            #.replace(">", "&gt;")
            #.replace("&", "&amp;")
            .replace(" ", "&nbsp")
            .replace("\n", "<br>")
        )
        self.html.append(f'<p><tt {style}>{code}</tt></p>')

    def error_color_style(self):
        return 'style = "color: #dd0000;"'

    def process_file_item(self, item: TestReport.Item):
        if not isinstance(item.file_content, File):
            self.html.append(f"<p {self.error_color_style()}>Expected File, but was:</p>")
            self.make_code(str(item.file_content), self.error_color_style())
            return
        if item.file_content.kind == File.Kind.Json or item.file_content.kind == File.Kind.Text:
            self.make_code(item.file_content.string_content)
        elif item.file_content.kind == File.Kind.Audio:
            b64 = base64.b64encode(item.file_content.content).decode("utf-8")
            html=f'''
            <audio controls>
                <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
                    <p {self.error_color_style()}>Your browser does not support the audio element.</p>
            </audio>'''
            self.html.append(html)
        elif item.file_content.kind == File.Kind.Image:
            b64 = base64.b64encode(item.file_content.content).decode("utf-8")
            img_tag = f'<img src="data:;base64,{b64}">'
            self.html.append(img_tag)
        else:
            self.html.append(f'<p {self.error_color_style()}>File.Kind {item.file_content.kind} is not yet supported</p>')


    def process_text_item(self, item: TestReport.Item):
        if item.is_code:
            return self.make_code(item.text_content)
        tag = 'p'
        if item.header_level is not None:
            tag=f'h{item.header_level+2}'
        self.html.append(f'<{tag}>{item.text_content}</{tag}>')


    def build(self, report: TestReport):
        self.html.append(f'<h1>{report.name}</h1>')
        for item in report.items:
            if item.text_content is not None:
                self.process_text_item(item)
            elif item.file_content is not None:
                self.process_file_item(item)
            else:
                self.html.append(f'<p {self.error_color_style()}>Cannot process item {item}</p>')

        if report.error is not None:
            self.html.append(f"<h1 {self.error_color_style()}><b>Exception</b></h1>")
            self.make_code(report.error, self.error_color_style())

        return "<html><body>"+"\n".join(self.html)+"</body></html>"


def create_self_test_report_page(report: TestReport):
    builder = Builder()
    return builder.build(report)