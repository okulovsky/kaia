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


class MDHandler:
    @staticmethod
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

    @staticmethod
    def parse_code(code: str, only_inside_functions: bool) -> list[CodeSection]:
        in_function = False
        in_comment = False
        sections = [CodeSection(False)]
        for line in code.split('\n'):
            sline = line.strip()

            if only_inside_functions:
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

    @staticmethod
    def write_sections(sections: list[CodeSection], require_indent: int = 0):
        INDENT = ' ' * require_indent
        result = []
        for s in sections:
            result.append('\n\n')
            if not s.is_comment:
                result.append('\n\n```python')
            for line in s.code:
                if line.strip() == '':
                    result.append('')
                else:
                    if not line.startswith(INDENT):
                        raise ValueError(f"Unexpected start of the line {line}")
                    result.append(line[require_indent:])
            if not s.is_comment:
                result.append('```\n\n')
        docu = '\n'.join(result)
        docu = re.sub(r'\n{3,}', '\n\n', docu)

        return docu


