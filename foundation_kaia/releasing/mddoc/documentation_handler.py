from pathlib import Path
from .parse import parse
from .toc import create_toc


def create_documentation(doc_folder: Path) -> str:
    blocks = []
    for file in sorted(doc_folder.glob('p*.py'), key=lambda f: f.name):
        blocks.extend(parse(file))

    parts = [b.to_md() for b in blocks if b.to_md().strip()]
    content = '\n\n'.join(parts)
    content = "# Table of contents\n\n" + create_toc(content) + '\n\n' + content
    return content
