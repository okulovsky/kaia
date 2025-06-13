from yo_fluq import Query, FileIO
from pathlib import Path
from foundation_kaia.releasing import MDHandler

def create_documentation():
    docu_root = Path(__file__).parent
    files = Query.folder(docu_root).where(lambda z: z.name.startswith('p')).order_by(lambda z: z.name).to_list()
    sections = []
    for file in files:
        text = FileIO.read_text(file)
        sections.extend(MDHandler.parse_code(text, True))


    template = FileIO.read_text(Path(__file__).parent/'readme_template.md')
    docu = MDHandler.write_sections(sections, 4)
    docu = template.replace('<<<FROM_TESTS>>>', docu)
    docu = "# Table of contents\n\n"+MDHandler.create_toc(docu) +'\n\n'+docu

    return docu


