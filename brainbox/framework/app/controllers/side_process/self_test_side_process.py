import html
import traceback

from .side_process_pool import ISideProcess
from pathlib import Path
from ....controllers import IController


class SelfTestSideProcess(ISideProcess):
    def __init__(self, controller: IController, self_test_folder:Path, api):
        self.controller = controller
        self.self_test_folder = self_test_folder
        self.api = api
        self._error: str | None = None

    def run(self):
        try:
            self.controller.self_test(self_test_folder=self.self_test_folder, api=self.api)
        except Exception:
            self._error = traceback.format_exc()

    def get_html_report(self) -> str:
        name = self.controller.get_name()
        report_path = self.self_test_folder / (name+'.html')
        sections = ''
        if report_path.is_file():
            try:
                with open(report_path, 'r') as f:
                    sections = f.read()
            except Exception:
                sections = f'<pre style="color:red">{html.escape(traceback.format_exc())}</pre>'
        if self._error:
            sections += f'<pre style="color:red">{html.escape(self._error)}</pre>'
        return sections or '<div>No report yet...</div>'
