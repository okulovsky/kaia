import base64
import html as _html
import json as _json
from dataclasses import dataclass
from typing import Any

from foundation_kaia.marshalling_2 import JSON, File
from foundation_kaia.logging import ILogItem


@dataclass
class ValueDocumentation:
    json: JSON|None
    file: File|None
    error: str|None = None


def _render_value(val: ValueDocumentation) -> str:
    if val.error is not None:
        return f'<span style="color:red">{_html.escape(val.error)}</span>'
    if val.file is not None:
        f = val.file
        if f.content is None:
            return f'<em>File: {_html.escape(f.name)} (no content)</em>'
        b64 = base64.b64encode(f.content).decode('ascii')
        ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
        if f.kind == File.Kind.Image:
            mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'bmp': 'image/bmp'}.get(ext, 'image/png')
            return f'<img src="data:{mime};base64,{b64}" style="max-width:400px">'
        if f.kind == File.Kind.Audio:
            mime = {'wav': 'audio/wav', 'mp3': 'audio/mpeg', 'ogg': 'audio/ogg'}.get(ext, 'audio/wav')
            return f'<audio controls><source src="data:{mime};base64,{b64}" type="{mime}"></audio>'
        try:
            text = f.content.decode('utf-8')
        except Exception:
            text = f'<binary {len(f.content)} bytes>'
        return f'<pre style="font-family:monospace">{_html.escape(text)}</pre>'

    if val.json is not None:
        if isinstance(val.json, (dict, list)):
            text = _json.dumps(val.json, indent=2, ensure_ascii=False, default=str)
        else:
            text = str(val.json)
        return f'<pre style="font-family:monospace">{_html.escape(text)}</pre>'

    return '<em>None</em>'


@dataclass
class LastCallDocumentation(ILogItem):
    decider: str
    parameter: str|None
    method: str|None
    arguments: dict[str, ValueDocumentation]
    result: ValueDocumentation|None
    log: tuple[str,...]
    error: str|None

    def to_string(self) -> str:
        return f'[CallTo: {self.decider}:{self.method}'

    def to_html(self) -> str:
        parts = []

        header = f'{_html.escape(self.decider)}::{_html.escape(self.method or "(default)")}'
        if self.parameter:
            header += f' ({_html.escape(self.parameter)})'
        parts.append(f'<p><strong>{header}</strong></p>')

        if self.arguments:
            parts.append('<h3>Arguments</h3>')
            parts.append('<table border="1" cellpadding="4"><tr><th>Name</th><th>Value</th></tr>')
            for name, val_doc in self.arguments.items():
                parts.append(f'<tr><td>{_html.escape(name)}</td><td>{_render_value(val_doc)}</td></tr>')
            parts.append('</table>')

        if self.log:
            log_text = _html.escape('\n'.join(self.log))
            parts.append(f'<details><summary>Log</summary><pre>{log_text}</pre></details>')

        if self.error:
            parts.append(f'<div style="color:red"><h3>Error</h3><pre>{_html.escape(self.error)}</pre></div>')

        if self.result is not None:
            parts.append('<h3>Result</h3>')
            parts.append(_render_value(self.result))

        return '\n'.join(parts)




