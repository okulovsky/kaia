from .text_fragment import TextFragment
from .collate import collate, DEFAULT_MIN_MATCH
from ..basics import BlockType, NodeData, ParagraphArray


def join_base(base: tuple[TextFragment[NodeData],...]) -> list[TextFragment[list[TextFragment[NodeData]]]]:
    joined: list[TextFragment[list[TextFragment[NodeData]]]] = []
    group: list[TextFragment[NodeData]] = []

    def flush():
        nonlocal group
        if len(group) > 0:
            joined.append(TextFragment(ParagraphArray.join(f.paragraphs for f in group), group))
            group = []

    for fragment in base:
        if fragment.payload.block_type == BlockType.Text:
            group.append(fragment)
        else:
            flush()
            joined.append(TextFragment(fragment.paragraphs, [fragment]))
    flush()
    return joined


def collate_sections(incoming: tuple[TextFragment[NodeData],...], base: tuple[TextFragment[NodeData],...], min_match: float = DEFAULT_MIN_MATCH):
    """
    In incoming, at this stage, we have big blocks. In the base, the text blocks are subdivided into smaller chunks
    To collate, we need to build joined_base, where consecutive text blocks are united into one TextFragment[list[TextFragment]],
    with original blocks given as stored data. Other blocks are tranformed to TextFragment(b.paragraphs, [b])
    Then, collate should be called to original incoming blocks and transformer base blocks.
    As a result, incloming blocks will receive match: a list of TextFragment with an original NodeData
    """
    joined_base = join_base(base)
    collate(incoming, tuple(joined_base), min_match)
