from .doc_block import IDockBlock, TextBlock, ExpectedValueBlock
from .code_block import CodeBlock
from .control_value import ControlValue
from pathlib import Path
import importlib.util
import re


class _Parser:
    def __init__(self, control_values: dict):
        self.control_values = control_values
        self.blocks: list[IDockBlock] = []
        self.pending_lines: list[str] = []
        self.pending_type: str | None = None   # 'code' | 'text'
        self._dispatch = self.in_code_mode

    def flush(self):
        if self.pending_lines:
            if self.pending_type == 'code':
                self.blocks.append(CodeBlock(self.pending_lines))
            else:
                self.blocks.append(TextBlock(self.pending_lines))
        self.pending_lines = []
        self.pending_type = None

    def accumulate(self, line: str, kind: str):
        if self.pending_type != kind:
            self.flush()
            self.pending_type = kind
        self.pending_lines.append(line)

    def make_expected_value_block(self, line: str) -> ExpectedValueBlock:
        m = re.match(r'\s*(\w+)\.mddoc_validate_control_value\(', line)
        return ExpectedValueBlock(line, self.control_values[m.group(1)].value)

    def dispatch(self, line: str):
        self._dispatch(line)

    def in_code_mode(self, line: str):
        stripped = line.strip()
        if stripped in ("'''", '"""'):
            self.flush()
            self._dispatch = self.in_text_mode
        elif 'mddoc_define_control_value' in line:
            pass #ignoring this line, not disrupting the block
        elif 'mddoc_validate_control_value' in line:
            self.flush()
            self.blocks.append(self.make_expected_value_block(line))
        else:
            self.accumulate(line, 'code')

    def in_text_mode(self, line: str):
        stripped = line.strip()
        if stripped in ("'''", '"""'):
            self.flush()
            self._dispatch = self.in_code_mode
        elif stripped.startswith('```'):
            self.flush()
            self._dispatch = self.in_code_inside_text_mode
        else:
            self.accumulate(line, 'text')

    def in_code_inside_text_mode(self, line: str):
        stripped = line.strip()
        if stripped == '```':
            self.flush()
            self._dispatch = self.in_text_mode
        elif stripped in ("'''", '"""'):
            raise ValueError("'''/\"\"\" cannot appear in the code blocks that are inside text blocks")
        else:
            self.accumulate(line, 'code')


def parse(file: Path) -> list[IDockBlock]:
    spec = importlib.util.spec_from_file_location('_mddoc_target', file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    control_values = {k: v for k, v in vars(module).items() if isinstance(v, ControlValue)}

    parser = _Parser(control_values)
    for line in file.read_text().splitlines():
        parser.dispatch(line)
    parser.flush()
    blocks = parser.blocks
    if blocks and isinstance(blocks[0], CodeBlock):
        blocks = blocks[1:]
    return blocks