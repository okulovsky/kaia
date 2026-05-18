from dataclasses import dataclass
from .log_item import ILogItem


@dataclass
class HtmlLogItem(ILogItem):
    html_content: str

    def to_html(self) -> str:
        return self.html_content

    def to_string(self) -> str:
        return '[html snippet]'
