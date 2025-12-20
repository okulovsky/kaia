import json
from dataclasses import dataclass
from .log_item import ILogItem
from typing import Any
from pprint import pformat
import traceback

@dataclass
class HeaderItem(ILogItem):
    level: int
    caption: str

    def to_html(self):
        return f'<h{self.level+1}>{self.caption}</h{self.level+1}>'

    def to_string(self) -> str:
        return '#'*(self.level+1) + ' ' + self.caption

@dataclass
class LineItem(ILogItem):
    text: str

    def to_html(self):
        return f'<p>{self.text}</p>'

    def to_string(self) -> str:
        return self.text


@dataclass
class ObjectItem(ILogItem):
    object: Any

    def _tostr(self):
        try:
            return json.dumps(self.object, ensure_ascii=False)
        except:
            return pformat(self.object)

    def to_html(self) -> str:
        return '<pre>'+self._tostr()+'</pre>'

    def to_string(self) -> str:
        return self._tostr()


@dataclass
class ExceptionItem(ILogItem):
    exception: BaseException

    def _tostr(self):
        return "\n".join(traceback.format_exception(self.exception))

    def to_html(self) -> str:
        return '<pre>'+self._tostr()+'</pre>'

    def to_string(self) -> str:
        return self._tostr()
