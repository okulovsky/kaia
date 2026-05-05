from pathlib import Path
from .parse import parse
from .toc import create_toc
from .doc_block import InsertMdFile


def create_documentation(doc_folder: Path) -> str:
    blocks = []
    for file in sorted(doc_folder.glob('doc_*.*'), key=lambda f: f.name):
        if file.name.endswith('.md'):
            blocks.append(InsertMdFile(file.read_text()))
        else:
            blocks.extend(parse(file))

    parts = [b.to_md() for b in blocks if b.to_md().strip()]
    content = '\n\n'.join(parts)
    content = "# Table of contents\n\n" + create_toc(content) + '\n\n' + content
    return content
