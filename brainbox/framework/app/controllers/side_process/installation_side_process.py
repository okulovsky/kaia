import html
import traceback
from datetime import datetime

from foundation_kaia.logging import Logger

from ..logging import LoggingLocalExecutor, LoggingApiCallback
from .side_process_pool import ISideProcess


class InstallationSideProcess(ISideProcess):
    def __init__(self, controller):
        self.controller = controller
        self._log: list[tuple[datetime, str]] = []
        self._error: str | None = None

    def run(self):
        callback = None
        try:
            self.controller.context._executor = LoggingLocalExecutor()
            self.controller.context._api_callback = LoggingApiCallback()

            def on_item(item):
                self._log.append((datetime.now(), item.to_string()))

            callback = on_item
            Logger.ON_ITEM.append(on_item)
            self.controller.install()
        except Exception:
            self._error = traceback.format_exc()
        finally:
            if callback is not None and callback in Logger.ON_ITEM:
                Logger.ON_ITEM.remove(callback)

    def get_html_report(self) -> str:
        lines = []
        for ts, text in self._log:
            lines.append(
                f'<div><span style="color:#888">{ts.strftime("%H:%M:%S")}</span> {html.escape(text)}</div>'
            )
        if self._error:
            lines.append(f'<pre style="color:red">{html.escape(self._error)}</pre>')
        return ''.join(lines) or '<div>No output yet...</div>'
