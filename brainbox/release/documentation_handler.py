from yo_fluq import Query, FileIO
from pathlib import Path
from dataclasses import dataclass, field
import re
import md_toc
from brainbox.framework import Loc

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


def create_toc(content: str):
    toc = []
    for line in content.split('\n'):
        if not line.startswith('#'):
            continue
        cnt = 0
        while line.startswith('#'*cnt):
            cnt+=1
        title = line[cnt:].strip()
        link = title.lower().replace(' ','-')
        toc.append('  '*(cnt-2)+f'* [{title}](#{link})')
    return "\n".join(toc)




def create_documentation():
    docu_root = Path(__file__).parent.parent/'doc'
    files = Query.folder(docu_root).where(lambda z: z.name.startswith('p')).order_by(lambda z: z.name).to_list()
    sections = []
    for file in files:
        text = FileIO.read_text(file)
        sections.extend(parse_code(text))


    template = FileIO.read_text(Path(__file__).parent/'readme_template.md')
    docu = write_docu(sections)
    docu = template.replace('<<<FROM_TESTS>>>', docu)
    docu = "# Table of contents\n\n"+create_toc(docu) +'\n\n'+docu

    FileIO.write_text(docu, Path(__file__).parent.parent/'README.md')
    return docu





if __name__ == '__main__':
    create_documentation()