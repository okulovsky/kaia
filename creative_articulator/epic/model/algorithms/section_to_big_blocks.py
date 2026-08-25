import uuid
from .text_fragment import TextFragment
from ..basics import BlockType, NodeData, NodeType, ParagraphArray, ParagraphType


def _block_type(paragraph) -> int|None:
    if paragraph.text_type == ParagraphType.Blank:
        return None
    if paragraph.text_type in (ParagraphType.Header, ParagraphType.Separator):
        return BlockType.Caption
    if paragraph.text_type == ParagraphType.Plan:
        return BlockType.Plan
    return BlockType.Text


def _to_fragment(paragraphs: list, block_type: int|None) -> TextFragment[NodeData]:
    array = ParagraphArray(*paragraphs)
    if block_type is None:
        block_type = BlockType.Text
    data = NodeData(
        NodeType.Block,
        uuid.uuid4().hex,
        None,
        array.simhash,
        block_type
    )
    return TextFragment(array, data)


def section_to_big_blocks(section: ParagraphArray) -> list[TextFragment]:
    """
    The section must be devided into blocks:
    Captions and separators always go to the block that only contains captions and separators. These blocks have BlockType Caption

    Plan also go to their exclusive block. Plan with the indent 1 always opens the block (so, no 2 plan lines with indent 1 coexist in one block)

    The rest go for the blocks that are not yet divided
    """
    blocks: list[TextFragment[NodeData]] = []
    current: list = []
    current_type: int|None = None

    for paragraph in section:
        block_type = _block_type(paragraph)
        if block_type is None:
            current.append(paragraph)
            continue
        opens_block = block_type == BlockType.Plan and paragraph.indent == 1
        if len(current) > 0 and current_type is not None and (current_type != block_type or opens_block):
            blocks.append(_to_fragment(current, current_type))
            current = []
        current.append(paragraph)
        current_type = block_type

    if len(current) > 0:
        blocks.append(_to_fragment(current, current_type))
    return blocks
