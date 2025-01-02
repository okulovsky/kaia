from yo_fluq import Query, FileIO
from pathlib import Path
from dataclasses import dataclass, field
import re

@dataclass
class CodeSection:
    is_comment: bool
    code: list[str] = field(default_factory=list)
    def is_empty(self):
        for c in self.code:
            if c.strip() != '':
                return False
        return True

    def debug_print(self):
        print(self.is_comment, '//'.join(self.code)[:100])


def parse_code(code: str):
    in_function = False
    in_comment = False
    sections = [CodeSection(False)]
    for line in code.split('\n'):
        sline = line.strip()
        if sline.startswith('def'):
            in_function = True
            continue
        if not in_function:
            continue
        if sline == "'''" or sline == '"""':
            in_comment = not in_comment
            sections.append(CodeSection(in_comment))
            continue
        sections[-1].code.append(line)

    sections = [s for s in sections if not s.is_empty()]
    return sections


def write_docu(sections: list[CodeSection]):
    result = []
    for s in sections:
        result.append('\n\n')
        if not s.is_comment:
            result.append('\n\n```python')
        for line in s.code:
            if line.strip() == '':
                result.append('')
            else:
                if not line.startswith('    '):
                    raise ValueError(f"Unexpected start of the line {line}")
                result.append(line[4:])
        if not s.is_comment:
            result.append('```\n\n')
    docu = '\n'.join(result)
    docu = re.sub(r'\n{3,}', '\n\n', docu)
    return docu



def create_documentation():
    docu_root = Path(__file__).parent.parent/'doc'
    files = Query.folder(docu_root).where(lambda z: z.name.startswith('p')).order_by(lambda z: z.name).to_list()
    sections = []
    for file in files:
        text = FileIO.read_text(file)
        sections.extend(parse_code(text))

    docu = write_docu(sections)
    template = FileIO.read_text(Path(__file__).parent/'readme_template.md')
    template = template.replace('<<<FROM_TESTS>>>', docu)
    FileIO.write_text(template, Path(__file__).parent.parent/'README.md')
    return template





if __name__ == '__main__':
    create_documentation()