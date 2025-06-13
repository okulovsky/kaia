from pathlib import Path
from yo_fluq import Query, FileIO
from foundation_kaia.releasing import MDHandler, CodeSection



def create_documentation():
    docu_root = Path(__file__).parent
    files = Query.folder(docu_root).where(lambda z: z.name.startswith('example')).order_by(lambda z: z.name).to_list()
    sections = []
    for file in files:
        text = FileIO.read_text(file)
        sections.extend(MDHandler.parse_code(text, False))

    template = FileIO.read_text(Path(__file__).parent/'readme_template.md')
    docu = MDHandler.write_sections(sections)
    docu = template.replace('<<<FROM_DEMO>>>', docu)
    docu = "# Table of contents\n\n"+MDHandler.create_toc(docu) +'\n\n'+docu

    return docu