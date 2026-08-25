import uuid
from ..basics import NodeData, NodeType, ParagraphArray, ParagraphType
from .text_fragment import TextFragment

_OPENING_TYPES = (ParagraphType.Header, ParagraphType.Separator)


def _is_meaningful(paragraph) -> bool:
    return paragraph.text_type not in (ParagraphType.Header, ParagraphType.Separator, ParagraphType.Blank)


def _title(paragraphs: ParagraphArray) -> str|None:
    for paragraph in paragraphs:
        if paragraph.text_type == ParagraphType.Header:
            return paragraph.title
    return None


def _to_fragment(paragraphs: list) -> TextFragment[NodeData]:
    array = ParagraphArray(*paragraphs)
    data = NodeData(
        NodeType.Section,
        uuid.uuid4().hex,
        _title(array),
        array.simhash
    )
    return TextFragment(array, data)


def file_to_sections(paragraphs: ParagraphArray) -> list[TextFragment]:
    """
    Must parse the file by # line, ## line, and line *** . Each of those should start the new section, if the previous section is not empty and does not consist from header only

    The headline/separator should go to the opened section

    NodeData should be constructed fully: name comes from header (if exists, otherwise None), id from guid, simhash must be computed

    """
    sections: list[TextFragment[NodeData]] = []
    current: list = []
    for paragraph in paragraphs:
        if paragraph.text_type in _OPENING_TYPES and any(_is_meaningful(p) for p in current):
            sections.append(_to_fragment(current))
            current = []
        current.append(paragraph)
    if len(current) > 0:
        sections.append(_to_fragment(current))
    return sections
